import pytest

import llm
from extraction import ExtractionError, extract, role_families
from helpers import GOOD, fake, vocab


def test_role_families(cv):
    assert role_families(cv) == ["ml-engineer", "data-engineer", "other"]


def test_extract_adds_metadata(cv, tmp_path):
    out = extract("texto", cv, vocab(cv, tmp_path), complete=fake(GOOD))
    assert out["schema_version"] == 1 and out["model"] == llm.EXTRACTION_MODEL
    assert out["extracted_at"] and out["role_family"] == "data-engineer"


def test_prompt_carries_text_families_and_vocabulary(cv, tmp_path):
    complete = fake(GOOD)
    extract("OFERTA-XYZ", cv, vocab(cv, tmp_path), complete=complete)
    assert all(s in complete.prompts[0] for s in ("OFERTA-XYZ", "data-engineer", "other", "Kubernetes"))


def test_schema_is_strict_and_lists_the_families(cv, tmp_path):
    complete = fake(GOOD)
    extract("t", cv, vocab(cv, tmp_path), complete=complete)
    schema = complete.schemas[0]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["properties"]["role_family"]["enum"] == ["ml-engineer", "data-engineer", "other"]


def test_invalid_family_is_retried_once(cv, tmp_path):
    complete = fake({**GOOD, "role_family": "astronauta"}, GOOD)
    assert extract("t", cv, vocab(cv, tmp_path), complete=complete)["role_family"] == "data-engineer"
    assert len(complete.prompts) == 2 and "astronauta" in complete.prompts[1]


def test_two_invalid_answers_fail(cv, tmp_path):
    bad = {**GOOD, "seniority": "ninja"}
    with pytest.raises(ExtractionError, match="seniority"):
        extract("t", cv, vocab(cv, tmp_path), complete=fake(bad, bad))


def test_skill_without_canonical_is_invalid(cv, tmp_path):
    bad = {**GOOD, "skills_required": [{"term": "dbt", "canonical": ""}]}
    with pytest.raises(ExtractionError):
        extract("t", cv, vocab(cv, tmp_path), complete=fake(bad, bad))
