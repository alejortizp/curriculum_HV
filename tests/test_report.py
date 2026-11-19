from report import skill_weight


def test_weight_grows_with_required_count():
    assert skill_weight(3, 0, "covered") > skill_weight(1, 0, "covered")


def test_one_required_mention_is_worth_two_nice_ones():
    assert skill_weight(1, 0, "covered") == skill_weight(0, 2, "covered")


def test_state_does_not_change_the_weight():
    assert skill_weight(2, 1, "covered") == skill_weight(2, 1, "mentioned") == skill_weight(2, 1, "gap")


def test_skill_nobody_asks_for_weighs_nothing():
    assert skill_weight(0, 0, "covered") == 0


from datetime import date

import offers_cli
from helpers import mk, vocab
from report import build_report, render_markdown, write_report

F = "data-engineer"


def test_counts_required_and_nice_per_offer(cv, tmp_path):
    r = build_report([mk("a", F, ["Python", "K8s"]), mk("b", F, ["python"], nice=["Snowflake"])],
                     F, vocab(cv, tmp_path, aliases={"K8s": "Kubernetes"}))
    by = {s["canonical"]: s for s in r["skills"]}
    assert (by["Python"]["required"], by["Python"]["state"]) == (2, "covered")
    assert by["Kubernetes"]["required"] == 1
    assert (by["Snowflake"]["nice"], by["Snowflake"]["state"]) == (1, "gap")


def test_same_skill_twice_in_one_offer_counts_once(cv, tmp_path):
    r = build_report([mk("a", F, ["Python", "python"], nice=["PYTHON"])], F, vocab(cv, tmp_path))
    assert (r["skills"][0]["required"], r["skills"][0]["nice"]) == (1, 0)


def test_skills_are_ordered_by_weight_then_name(cv, tmp_path):
    r = build_report([mk("a", F, ["SQL", "Go"], nice=["Python"]), mk("b", F, ["Go"])], F, vocab(cv, tmp_path))
    assert [s["canonical"] for s in r["skills"]] == ["Go", "SQL", "Python"]


def test_coverage_is_share_of_required_that_are_not_gaps(cv, tmp_path):
    r = build_report([mk("a", F, ["Python", "Pandas", "Snowflake", "dbt"])], F, vocab(cv, tmp_path))
    assert r["offers"][0]["coverage"] == 0.5


def test_offer_without_required_skills_has_no_coverage(cv, tmp_path):
    assert build_report([mk("a", F, [])], F, vocab(cv, tmp_path))["offers"][0]["coverage"] is None


def test_other_families_and_pending_are_excluded(cv, tmp_path):
    pending = {"id": "p", "added": "2026-11-01", "extraction": None}
    r = build_report([mk("a", F, ["Python"]), mk("b", "mlops", ["Go"]), pending], F, vocab(cv, tmp_path))
    assert r["n_offers"] == 1 and r["pending"] == ["p"]


def test_since_filters_by_added(cv, tmp_path):
    r = build_report([mk("a", F, ["Python"], added="2026-01-01"), mk("b", F, ["Go"], added="2026-06-01")],
                     F, vocab(cv, tmp_path), since=date(2026, 3, 1))
    assert [o["id"] for o in r["offers"]] == ["b"] and r["date_range"] == ["2026-06-01", "2026-06-01"]


def test_weak_signal_below_ten_offers(cv, tmp_path):
    nine = [mk(f"o{i}", F, ["Python"]) for i in range(9)]
    assert build_report(nine, F, vocab(cv, tmp_path))["weak_signal"] is True
    assert build_report(nine + [mk("o9", F, ["Go"])], F, vocab(cv, tmp_path))["weak_signal"] is False


def test_general_term_shows_backing(cv, tmp_path):
    r = build_report([mk("a", F, ["Lakehouse"])], F, vocab(cv, tmp_path, general_terms={"Lakehouse": ["Delta Lake"]}))
    assert r["skills"][0]["backing"] == ["Delta Lake"] and r["skills"][0]["state"] == "covered"


def test_seniority_years_and_languages(cv, tmp_path):
    r = build_report([mk("a", F, [], years_required=2), mk("b", F, [], years_required=5, seniority=None, language="en"),
                      mk("c", F, [], years_required=None)], F, vocab(cv, tmp_path))
    assert r["seniority"] == {"senior": 2} and r["years_required_median"] == 3.5
    assert r["languages"] == {"es": 2, "en": 1} and r["languages_required"] == {"en B2": 3}
    assert r["responsibilities"][0] == {"offer_id": "a", "items": ["Construir pipelines."]}


def test_markdown_lists_gaps_and_warns(cv, tmp_path):
    md = render_markdown(build_report([mk("a", F, ["Snowflake", "Pandas", "Python"])], F, vocab(cv, tmp_path)))
    assert "Snowflake" in md and "señal débil" in md.lower()
    assert md.index("## Vacíos") < md.index("## Mencionadas") < md.index("## Cubiertas")


def test_empty_family_report(cv, tmp_path):
    r = build_report([], F, vocab(cv, tmp_path))
    assert r["n_offers"] == 0 and r["skills"] == [] and r["date_range"] is None
    assert "0 ofertas" in render_markdown(r)


def test_write_report_creates_both_files(cv, tmp_path):
    json_path, md_path = write_report(build_report([mk("a", F, ["Python"])], F, vocab(cv, tmp_path)), tmp_path / "out")
    assert json_path.name == "report.json" and md_path.name == "report.md" and md_path.read_text().startswith("# ")


def test_report_command_writes_one_report_per_family_with_offers(offers_dir, cv_file, tmp_path):
    from helpers import GOOD, fake
    offers_cli.cmd_add("uno", complete=fake(GOOD))
    paths = offers_cli.cmd_report(out_root=tmp_path / "market")
    assert [p.parent.name for p in paths] == ["data-engineer"] and paths[0].name == "report.md"
    assert offers_cli.cmd_report(family="ml-engineer", out_root=tmp_path / "market")[0].read_text().count("0 ofertas") == 1
