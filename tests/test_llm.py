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
