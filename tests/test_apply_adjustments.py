import copy

import pytest

import build

ADJ = {
    "lang": "es",
    "summary": "Resumen nuevo.",
    "experience_order": ["Salud SA", "Acme"],
    "experience": {"Acme": ["nueva"]},
}


def test_does_not_mutate_input(cv):
    before = copy.deepcopy(cv)
    build.apply_adjustments(cv, {**ADJ, "projects_shown": ["Sistema B"],
                                 "tech_stack_order": [{"category": "Cloud", "first": ["DynamoDB"]}]})
    assert cv == before


def test_summary_title_order_and_bullets(cv):
    out = build.apply_adjustments(cv, {**ADJ, "title": "Data Engineer | Machine Learning Engineer"})
    assert out["profile"] == {"es": ADJ["summary"]}
    assert out["personal"]["title"] == "Data Engineer | Machine Learning Engineer"
    assert [e["company"] for e in out["experience"]] == ["Salud SA", "Acme"]
    assert out["experience"][1]["items"]["es"] == ["nueva"]
    assert out["experience"][1]["items"]["en"] == cv["experience"][0]["items"]["en"]


def test_without_title_the_base_title_is_kept(cv):
    assert build.apply_adjustments(cv, ADJ)["personal"]["title"] == cv["personal"]["title"]


def test_entry_missing_from_order_keeps_position_at_end(cv):
    out = build.apply_adjustments(cv, {**ADJ, "experience_order": ["Salud SA"]})
    assert [e["company"] for e in out["experience"]] == ["Salud SA", "Acme"]


def test_tech_stack_order_reorders_without_changing_the_set(cv):
    out = build.apply_adjustments(cv, {**ADJ, "tech_stack_order": [
        {"category": "Cloud", "first": ["DynamoDB"]},
        {"category": "Datos", "first": ["Go", "Delta Lake"]}]})
    assert [c["category"] for c in out["tech_stack"]] == ["Cloud", "Datos"]
    assert [line[0]["name"] for line in out["tech_stack"][0]["items"]] == ["DynamoDB", "Kubernetes"]
    assert [line[0]["name"] for line in out["tech_stack"][1]["items"]] == [
        "Go", "Delta Lake", "Python", "Databricks + MLflow"]


def test_groups_not_listed_keep_their_order_after_the_listed_ones(cv):
    out = build.apply_adjustments(cv, {**ADJ, "tech_stack_order": [{"category": "Cloud", "first": []}]})
    assert [c["category"] for c in out["tech_stack"]] == ["Cloud", "Datos"]


def test_projects_shown_can_reveal_a_hidden_project(cv):
    out = build.apply_adjustments(cv, {**ADJ, "projects_shown": ["Sistema B"]})
    assert [(p["title"]["es"], p["cv"]) for p in out["projects"]] == [("Sistema B", True), ("Agente A", False)]


def test_without_projects_shown_cv_flags_are_kept(cv):
    assert build.apply_adjustments(cv, ADJ)["projects"] == cv["projects"]


@pytest.mark.parametrize("patch,name", [
    ({"experience": {"Nadie": ["x"]}}, "Nadie"),
    ({"experience_order": ["Nadie", "Acme", "Salud SA"]}, "Nadie"),
    ({"tech_stack_order": [{"category": "Nube", "first": []}]}, "Nube"),
    ({"tech_stack_order": [{"category": "Datos", "first": ["Rust"]}]}, "Rust"),
    ({"projects_shown": ["Fantasma"]}, "Fantasma"),
    ({"academic_shown": ["Fantasma"]}, "Fantasma"),
])
def test_unknown_names_raise(cv, patch, name):
    with pytest.raises(ValueError, match=name):
        build.apply_adjustments(cv, {**ADJ, **patch})


def test_repeated_company_is_an_error(cv):
    cv["experience"].append(copy.deepcopy(cv["experience"][0]))
    with pytest.raises(ValueError, match="Acme"):
        build.apply_adjustments(cv, ADJ)
