import json

import pytest

import extraction
import llm
import offers
import offers_cli
import session
import tailor
from helpers import BAD_SUMMARY, GOOD, RESP, TARGET
from session import AwaitingResponse, SessionError, exchange

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["ok", "items"],
          "properties": {"ok": {"type": "boolean"},
                         "items": {"type": "array", "items": {"type": "string"}}}}


def ask(folder, prompt="pregunta"):
    return exchange(folder, "paso")(prompt, SCHEMA, model="m", effort="low")


def test_without_a_response_the_prompt_is_written_and_the_step_waits(tmp_path):
    with pytest.raises(AwaitingResponse) as exc:
        ask(tmp_path)
    assert exc.value.prompt_path == tmp_path / "paso.prompt.md"
    assert exc.value.response_path == tmp_path / "paso.response.json"
    assert "pregunta" in exc.value.prompt_path.read_text()
    assert json.loads((tmp_path / "paso.schema.json").read_text()) == SCHEMA


def test_a_written_response_is_returned(tmp_path):
    with pytest.raises(AwaitingResponse):
        ask(tmp_path)
    (tmp_path / "paso.response.json").write_text('{"ok": true, "items": ["a"]}')
    assert ask(tmp_path) == {"ok": True, "items": ["a"]}
    assert ask(tmp_path) == {"ok": True, "items": ["a"]}      # repetible


def test_a_response_to_an_older_prompt_is_discarded(tmp_path):
    with pytest.raises(AwaitingResponse):
        ask(tmp_path)
    (tmp_path / "paso.response.json").write_text('{"ok": true, "items": []}')
    with pytest.raises(AwaitingResponse):
        ask(tmp_path, prompt="otra pregunta")
    assert not (tmp_path / "paso.response.json").exists()
    assert "otra pregunta" in (tmp_path / "paso.prompt.md").read_text()


@pytest.mark.parametrize("text,fragment", [
    ("no es json", "JSON"),
    ('{"ok": true}', "items"),
    ('{"ok": "sí", "items": []}', "ok"),
    ('{"ok": true, "items": [1]}', "items"),
    ('{"ok": true, "items": [], "extra": 1}', "extra"),
])
def test_a_response_that_does_not_follow_the_schema_is_an_error(tmp_path, text, fragment):
    with pytest.raises(AwaitingResponse):
        ask(tmp_path)
    (tmp_path / "paso.response.json").write_text(text)
    with pytest.raises(SessionError, match=fragment):
        ask(tmp_path)


def test_the_session_is_the_default_provider_and_the_api_is_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setattr(session, "_dotenv", lambda key: "")
    complete, attempts = session.provider(tmp_path, "paso")
    assert attempts == 1 and complete is not llm.complete_json
    monkeypatch.setenv("LLM_PROVIDER", "api")
    assert session.provider(tmp_path, "paso") == (llm.complete_json, 2)


@pytest.fixture
def in_session(monkeypatch, tmp_path):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setattr(session, "_dotenv", lambda key: "")
    monkeypatch.setattr(offers_cli, "INBOX_DIR", tmp_path / "inbox")
    return tmp_path / "inbox"


def test_offer_add_in_session_saves_the_text_and_waits_for_the_extraction(offers_dir, cv_file, in_session):
    with pytest.raises(AwaitingResponse) as exc:
        offers_cli.cmd_add("texto de la oferta")
    [pending] = offers.list_offers()
    assert pending["extraction"] is None
    assert exc.value.prompt_path.parent == in_session / pending["id"]

    exc.value.response_path.write_text(json.dumps(GOOD))
    [done] = offers_cli.cmd_extract()
    assert done["extraction"]["role_family"] == "data-engineer" and "-pendiente-" not in done["id"]
    assert not (in_session / pending["id"]).exists()          # el intercambio se limpia


def test_invalid_extraction_in_session_is_not_retried(offers_dir, cv_file, in_session):
    with pytest.raises(AwaitingResponse) as exc:
        offers_cli.cmd_add("texto de la oferta")
    exc.value.response_path.write_text(json.dumps({**GOOD, "seniority": "ninja"}))
    # the schema check catches it first; either way it is reported once, with the field
    with pytest.raises((session.SessionError, extraction.ExtractionError), match="seniority"):
        offers_cli.cmd_extract()
    assert offers.list_offers()[0]["extraction"] is None


def test_apply_in_session_waits_then_renders(tmp_path, cv_file, in_session):
    out = tmp_path / "salida"
    with pytest.raises(AwaitingResponse) as exc:
        tailor.run(TARGET, out, html_only=True)
    assert exc.value.prompt_path == out / "tailoring.prompt.md"
    exc.value.response_path.write_text(json.dumps(RESP))
    tailor.run(TARGET, out, html_only=True)
    assert (out / "adjustments.json").exists() and list(out.glob("CV-*.html"))


def test_rejected_answer_in_session_is_reported_without_a_second_prompt(tmp_path, cv_file, in_session):
    out = tmp_path / "salida"
    with pytest.raises(AwaitingResponse) as exc:
        tailor.run(TARGET, out, html_only=True)
    before = exc.value.prompt_path.read_text()
    exc.value.response_path.write_text(json.dumps({**RESP, "summary": BAD_SUMMARY}))
    with pytest.raises(tailor.Rejected):
        tailor.run(TARGET, out, html_only=True)
    assert exc.value.prompt_path.read_text() == before and exc.value.response_path.exists()
    assert json.loads((out / "adjustments.rejected.json").read_text())["reasons"]
