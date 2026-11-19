import json

import pytest

import tailor
import targets
from helpers import RESP, RESP_NO_LETTER, TARGET, fake, rename_company, seed_offer
from tailor import Rejected, generate, material, run

BAD = {**RESP, "summary": "Experto en Snowflake."}


def test_material_has_every_hand_written_variant(cv):
    m = material(cv, "es")
    acme = next(e for e in m["experience"] if e["company"] == "Acme")
    assert len(acme["variants"]) == 2
    assert set(m["titles"]) == {"AI Engineer | Machine Learning Engineer", "Data Engineer | Machine Learning Engineer"}
    assert {p["title"] for p in m["projects"]} == {"Agente A", "Sistema B"}     # incluye el oculto
    assert set(m["summaries"]) == {"default", "ml-engineer", "data-engineer"}
    assert [e["company"] for e in material(cv, "en")["experience"]] == ["Acme"]


def test_generate_converts_lists_and_sets_profile_in_code(cv):
    adj, letter = generate(cv, TARGET, complete=fake(RESP))
    assert adj["experience"] == {"Acme": RESP["experience"][0]["bullets"]}
    assert adj["profile"] == TARGET["profile"] and adj["lang"] == "es"
    assert adj["target"] == {"kind": "offer", "id": TARGET["id"]}
    assert adj["projects_shown"] == ["Sistema B"] and "academic_shown" not in adj
    assert letter["opening"] == {"es": RESP["cover_letter"]["opening"]}
    assert letter["company"] == "Globex" and letter["why_me"] == {"es": RESP["cover_letter"]["why_me"]}


def test_prompt_and_schema_follow_the_target(cv):
    complete = fake(RESP)
    generate(cv, TARGET, complete=complete)
    prompt, schema = complete.prompts[0], complete.schemas[0]
    assert all(s in prompt for s in ("Snowflake", "Buscamos Data Engineer", "Despliegue en", "Sistema B"))
    assert "cover_letter" in schema["properties"] and schema["additionalProperties"] is False
    family = fake(RESP_NO_LETTER)
    generate(cv, {**TARGET, "kind": "family", "source_text": None}, complete=family)
    assert "cover_letter" not in family.schemas[0]["properties"]


def test_family_target_gets_no_cover_letter(cv):
    assert generate(cv, {**TARGET, "kind": "family", "source_text": None}, complete=fake(RESP_NO_LETTER))[1] is None


def test_rejected_answer_is_retried_once_with_reasons(cv):
    complete = fake(BAD, RESP)
    generate(cv, TARGET, complete=complete)
    assert len(complete.prompts) == 2 and "menciona el vacío" in complete.prompts[1]
    assert "menciona el vacío" not in complete.prompts[0]


def test_two_rejections_raise_with_reasons(cv):
    with pytest.raises(Rejected) as exc:
        generate(cv, TARGET, complete=fake(BAD, BAD))
    assert exc.value.reasons and exc.value.adjustments["summary"] == "Experto en Snowflake."


def test_run_writes_rejected_file_and_renders_nothing(tmp_path, cv_file):
    with pytest.raises(Rejected):
        run(TARGET, tmp_path, html_only=True, complete=fake(BAD, BAD))
    rejected = json.loads((tmp_path / "adjustments.rejected.json").read_text())
    assert rejected["reasons"] and not list(tmp_path.glob("*.html"))
    assert not (tmp_path / "adjustments.json").exists()


def test_run_html_only_writes_adjustments_and_html(tmp_path, cv_file):
    out = run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    assert (tmp_path / "adjustments.json").exists() and (tmp_path / "cover_letter.json").exists()
    assert out["pages"] is None
    [cv_html] = tmp_path.glob("CV-*.html")
    assert list(tmp_path.glob("Carta-*.html"))
    html = cv_html.read_text()
    assert "Despliegue en" in html and "Sistema B" in html and "Agente A" not in html


def test_render_only_revalidates_against_current_cv(tmp_path, cv_file):
    run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    rename_company(cv_file, "Acme", "Acme Corp")         # cv.json cambió después
    with pytest.raises(Rejected) as exc:
        run(TARGET, tmp_path, html_only=True, render_only=True, complete=fake())
    assert any("Acme" in r for r in exc.value.reasons)


def test_render_only_uses_hand_edited_adjustments(tmp_path, cv_file):
    run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    path = tmp_path / "adjustments.json"
    adj = json.loads(path.read_text())
    adj["summary"] = "Resumen editado a mano."
    path.write_text(json.dumps(adj, ensure_ascii=False))
    run(TARGET, tmp_path, html_only=True, render_only=True, complete=fake())
    assert "Resumen editado a mano." in next(tmp_path.glob("CV-*.html")).read_text()


def test_generated_html_has_no_api_key(tmp_path, cv_file, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSECRETO")
    run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    assert "AIzaSECRETO" not in next(tmp_path.glob("CV-*.html")).read_text()


def test_without_offer_or_family_explains_the_new_flow(capsys):
    with pytest.raises(SystemExit) as exc:
        tailor.main([])
    assert exc.value.code == 1 and "make apply OFFER=" in capsys.readouterr().out


# Entrega 4: CV por familia
def test_family_run_writes_report_and_cv_without_letter(tmp_path, cv_file, offers_dir):
    seed_offer("data-engineer", ["Python", "Snowflake"])
    out = tailor.main_family("data-engineer", tmp_path, lang="es", html_only=True, complete=fake(RESP_NO_LETTER))
    assert (tmp_path / "report.json").exists() and (tmp_path / "report.md").exists()
    assert (tmp_path / "adjustments.json").exists() and not list(tmp_path.glob("Carta-*"))
    assert out["weak_signal"] is True


def test_family_without_offers_fails_with_a_clear_message(tmp_path, cv_file, offers_dir):
    with pytest.raises(targets.TargetError, match="data-engineer"):
        tailor.main_family("data-engineer", tmp_path, lang="es", html_only=True, complete=fake())


def test_unknown_family_is_rejected(cv_file, offers_dir, capsys):
    with pytest.raises(SystemExit) as exc:
        tailor.main(["--family", "astronauta"])
    assert exc.value.code == 1 and "astronauta" in capsys.readouterr().out


def test_prompt_explains_how_the_letter_template_composes_its_fields(cv):
    # found in the first real run: the template prints "<greeting> <recipient>," and "<sign_off>,"
    complete = fake(RESP)
    generate(cv, TARGET, complete=complete)
    prompt = complete.prompts[0]
    assert "appends the recipient" in prompt and "appends a comma and the candidate's name" in prompt
