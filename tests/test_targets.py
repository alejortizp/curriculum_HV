import pytest

from helpers import mk, vocab
from report import build_report
from targets import TargetError, from_offer, from_report


def test_offer_target_classifies_skills(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"SnowSQL": "Snowflake"}, general_terms={"Lakehouse": ["Delta Lake"]})
    t = from_offer(mk("a", "data-engineer", ["Python", "Pandas", "Snowflake", "Lakehouse"], raw="TEXTO"), cv, v)
    assert t["kind"] == "offer" and t["id"] == "a" and t["profile"] == "data-engineer"
    assert t["source_text"] == "TEXTO" and t["context"] == {"company": "Empresa", "role": "Rol"}
    assert set(t["emphasize"]) == {"Python", "Pandas"}
    assert t["general_terms"] == {"Lakehouse": ["Delta Lake"]}
    assert t["gaps"] == [{"canonical": "Snowflake", "forms": ["Snowflake", "SnowSQL"]}]
    assert t["responsibilities"] == ["Construir pipelines."]


def test_emphasize_is_ordered_by_weight(cv, tmp_path):
    t = from_offer(mk("a", "data-engineer", ["SQL", "Go"], nice=["Python"]), cv, vocab(cv, tmp_path))
    assert t["emphasize"] == ["Go", "SQL", "Python"]


def test_general_term_lists_every_form_of_its_backing_skills(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"Databricks": "Databricks + MLflow"},
              general_terms={"Big Data": ["Databricks + MLflow"]})
    t = from_offer(mk("a", "data-engineer", ["Big Data"]), cv, v)
    assert t["general_terms"] == {"Big Data": ["Databricks + MLflow", "Databricks"]}


def test_other_family_uses_default_profile(cv, tmp_path):
    assert from_offer(mk("a", "other", ["Python"]), cv, vocab(cv, tmp_path))["profile"] == "default"


def test_language_defaults_to_offer_language_and_can_be_overridden(cv, tmp_path):
    o = mk("a", "data-engineer", ["Python"], language="en")
    assert from_offer(o, cv, vocab(cv, tmp_path))["lang"] == "en"
    assert from_offer(o, cv, vocab(cv, tmp_path), lang="es")["lang"] == "es"
    assert from_offer(mk("b", "other", [], language="other"), cv, vocab(cv, tmp_path))["lang"] == "es"


def test_pending_offer_cannot_be_a_target(cv, tmp_path):
    with pytest.raises(TargetError):
        from_offer({"id": "p", "extraction": None}, cv, vocab(cv, tmp_path))


def test_family_target_has_no_source_text(cv, tmp_path):
    v = vocab(cv, tmp_path)
    r = build_report([mk("a", "data-engineer", ["Python", "Snowflake"])], "data-engineer", v)
    t = from_report(r, cv, v, lang="en")
    assert t["kind"] == "family" and t["id"] == "data-engineer" and t["source_text"] is None and t["lang"] == "en"
    assert t["context"] == {"family": "data-engineer", "n_offers": 1}
    assert [g["canonical"] for g in t["gaps"]] == ["Snowflake"]


def test_empty_report_cannot_be_a_target(cv, tmp_path):
    v = vocab(cv, tmp_path)
    with pytest.raises(TargetError, match="data-engineer"):
        from_report(build_report([], "data-engineer", v), cv, v)


def test_every_declared_general_term_is_in_the_target_even_if_not_requested(cv, tmp_path):
    v = vocab(cv, tmp_path, general_terms={"Lakehouse": ["Delta Lake"], "NoSQL": ["DynamoDB"]})
    t = from_offer(mk("a", "data-engineer", ["Lakehouse"]), cv, v)
    assert t["general_terms"] == {"Lakehouse": ["Delta Lake"], "NoSQL": ["DynamoDB"]}
    assert "label" not in t
