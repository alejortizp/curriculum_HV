import pytest

from validator import entry_variants, hand_written_titles, validate

OK = {
    "lang": "es",
    "summary": "Ingeniera de datos con pipelines en <strong>Python</strong>.",
    "experience_order": ["Acme", "Salud SA"],
    "experience": {"Acme": ["Extracción con <strong>95%</strong> de precisión."]},
}
T = {
    "gaps": [{"canonical": "Snowflake", "forms": ["Snowflake", "SnowSQL"]}],
    "general_terms": {"Lakehouse": ["Delta Lake"]},
    "context": {"company": "Snowflake Inc", "role": "Snowflake Data Engineer"},
}


@pytest.fixture
def bad(cv):
    return lambda **patch: validate(cv, {**OK, **patch}, T)


def test_valid_adjustments_pass(cv):
    assert validate(cv, OK, T) == []


def test_variants_include_profile_overrides(cv):
    assert len(entry_variants(cv, "Acme", "es")) == 2
    assert len(entry_variants(cv, "Salud SA", "es")) == 1
    assert entry_variants(cv, "Salud SA", "en") == []


def test_hand_written_titles(cv):
    assert hand_written_titles(cv) == {
        "AI Engineer | Machine Learning Engineer", "Data Engineer | Machine Learning Engineer"}


# Regla 1: vacíos
def test_gap_term_or_alias_is_rejected(bad):
    assert any("Snowflake" in r for r in bad(summary="Experto en snowflake."))
    assert any("Snowflake" in r for r in bad(experience={"Acme": ["Consultas con SnowSQL."]}))


def test_company_and_role_are_exempt_in_the_letter_only(cv):
    letter = {"company": "Snowflake Inc", "role": "Snowflake Data Engineer",
              "opening": {"es": "Me postulo a Snowflake Data Engineer en Snowflake Inc."}}
    assert validate(cv, OK, T, letter) == []
    assert validate(cv, OK, T, {"opening": {"es": "Domino Snowflake."}}) != []
    assert validate(cv, {**OK, "summary": "Quiero ser Snowflake Data Engineer."}, T) != []


def test_family_target_without_company_or_role(cv):
    assert validate(cv, OK, {**T, "context": {"family": "data-engineer", "n_offers": 3}}) == []


# Regla 2: cifras
def test_figure_from_another_variant_of_the_same_entry_is_allowed(bad):
    assert bad(experience={"Acme": ["Despliegue en 2 días."]}) == []


def test_figure_outside_the_entry_is_rejected(bad):
    assert any("Acme" in r and "99" in r for r in bad(experience={"Acme": ["Mejora del 99%."]}))


def test_summary_figure_must_exist_in_cv_text(bad):
    assert bad(summary="Con 5+ años.") == []
    assert bad(summary="Con 12+ años.") != []


def test_letter_figures_are_checked_except_the_date(cv):
    assert validate(cv, OK, T, {"date": {"es": "19 de noviembre de 2099"}, "why_me": {"es": ["Con 95% de precisión."]}}) == []
    assert validate(cv, OK, T, {"why_me": {"es": ["Con 77% de precisión."]}}) != []


# Regla 3: número de viñetas
def test_more_bullets_than_longest_variant_is_rejected(bad):
    assert bad(experience={"Acme": ["a", "b", "c"]}) == []
    assert bad(experience={"Acme": ["a", "b", "c", "d"]}) != []


# Regla 4: empresas, orden y título
def test_unknown_company_and_title(bad):
    assert any("Nadie" in r for r in bad(experience={"Nadie": ["a"]}))
    assert bad(title="Data Engineer | Machine Learning Engineer") == []
    assert bad(title="Chief Everything Officer") != []


def test_order_must_list_every_entry_in_that_language(cv, bad):
    assert bad(experience_order=["Acme"]) != []
    assert bad(experience_order=["Acme", "Salud SA", "Acme"]) != []
    en = {**OK, "lang": "en", "experience_order": ["Acme"], "experience": {}}
    assert validate(cv, en, T) == []          # Salud SA solo existe en español
    assert validate(cv, {**en, "experience_order": ["Acme", "Salud SA"]}, T) != []


# Regla 5: orden de habilidades y proyectos
def test_unknown_group_skill_or_project(bad):
    assert bad(tech_stack_order=[{"category": "Datos", "first": ["Go"]}], projects_shown=["Sistema B"]) == []
    assert bad(tech_stack_order=[{"category": "Nube", "first": []}]) != []
    assert bad(tech_stack_order=[{"category": "Datos", "first": ["Rust"]}]) != []
    assert bad(projects_shown=["Fantasma"]) != []
    assert bad(academic_shown=["Fantasma"]) != []


# Regla 6: términos generales
def test_general_term_needs_a_backing_skill_in_the_same_text(bad):
    assert bad(summary="Arquitectura Lakehouse sobre Delta Lake.") == []
    assert any("Lakehouse" in r for r in bad(summary="Arquitectura Lakehouse."))
    assert bad(experience={"Acme": ["Diseñé el Lakehouse.", "Usé Delta Lake."]}) != []


# Etiquetas
def test_only_strong_and_em_are_allowed(bad):
    assert bad(summary="<strong>ok</strong> <em>ok</em>") == []
    assert bad(summary='<a href="http://x">enlace</a>') != []
    assert bad(experience={"Acme": ["<script>alert(1)</script>"]}) != []


def test_allowed_tags_cannot_carry_attributes(bad):
    assert bad(summary='<strong onmouseover="x()">a</strong>') != []
    assert bad(summary="<em/>a") != []
    assert bad(experience={"Acme": ["texto <img src=x onerror=alert(1)"]}) != []   # sin cerrar


def test_entity_for_less_than_is_fine_but_a_raw_one_is_not(bad):
    assert bad(experience={"Acme": ["precisión &lt;95%"]}) == []
    assert bad(summary="a &lt; b") == []
    assert bad(summary="a < b") != []


def test_every_letter_field_is_checked_for_markup(cv):
    for field in ("company", "role", "date"):
        assert validate(cv, OK, T, {field: "<script>x</script>"}) != []
        assert validate(cv, OK, T, {field: {"es": "<b>x</b>"}}) != []
    assert validate(cv, OK, T, {"company": "Snowflake Inc", "date": {"es": "19 de noviembre de 2026"}}) == []
