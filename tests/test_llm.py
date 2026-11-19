import pytest

import llm

SCHEMA = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


def test_missing_credentials_are_reported_as_llm_error(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(llm, "ROOT", tmp_path)          # no .env here
    llm._client.cache_clear()
    with pytest.raises(llm.LLMError, match="ANTHROPIC_API_KEY"):
        llm.complete_json("hola", SCHEMA, model=llm.EXTRACTION_MODEL, effort="low")
    llm._client.cache_clear()


def test_deterministic_modules_do_not_import_anthropic():
    import subprocess
    import sys
    code = ("import sys, offers, vocabulary, report, targets, validator, textutil; "
            "sys.exit('anthropic' in sys.modules)")
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


from types import SimpleNamespace

import anthropic


def answer(text, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="thinking"),
                                                      SimpleNamespace(type="text", text=text)])


def call(monkeypatch, outcome):
    def create(**kwargs):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "_client", lambda: client)
    return llm.complete_json("p", SCHEMA, model="m", effort="low")


def test_valid_answer_is_parsed(monkeypatch):
    assert call(monkeypatch, answer('{"ok": true}')) == {"ok": True}


@pytest.mark.parametrize("outcome,fragment", [
    (answer("", stop="refusal"), "rechazó"),
    (answer('{"ok": tr', stop="max_tokens"), "max_tokens"),
    (answer("esto no es json"), "JSON"),
])
def test_unusable_answers_are_llm_errors(monkeypatch, outcome, fragment):
    with pytest.raises(llm.LLMError, match=fragment):
        call(monkeypatch, outcome)


@pytest.mark.parametrize("cls,fragment", [
    (anthropic.AuthenticationError, "Credenciales"),
    (anthropic.RateLimitError, "Límite"),
    (anthropic.InternalServerError, "500"),
    (anthropic.APIConnectionError, "conexión"),
])
def test_sdk_errors_are_mapped_to_one_line(monkeypatch, cls, fragment):
    error = cls.__new__(cls)                 # the SDK constructors need a live request
    error.status_code, error.message = 500, "fallo"
    with pytest.raises(llm.LLMError, match=fragment):
        call(monkeypatch, error)
