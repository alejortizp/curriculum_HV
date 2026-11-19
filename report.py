"""Market report for a role family: deterministic counting, no model involved."""

import json
import statistics
from collections import Counter
from datetime import date
from pathlib import Path

from vocabulary import COVERED, GAP, MENTIONED, Vocabulary

ROOT = Path(__file__).parent
MARKET_DIR = ROOT / "applications" / "_market"
MIN_OFFERS = 10  # below this, the report warns that the signal is weak


def skill_weight(required: int, nice: int, state: str) -> float:
    """Weight used to order a skill in the report and in a target.

    Market demand only: a required mention counts double a nice-to-have one, and
    the state (covered, mentioned, gap) does not change it, so the report shows
    what offers ask for most regardless of what the CV already lists.
    """
    return 2 * required + nice


def _canonicals(skills: list[dict], vocab: Vocabulary) -> set[str]:
    return {vocab.canonical(s["term"], s.get("canonical")) for s in skills or []}


def build_report(offers: list[dict], family: str, vocab: Vocabulary,
                 since: date | None = None) -> dict:
    """Count what the offers of one family ask for and how the CV stands against it."""
    in_range = [o for o in offers if since is None or date.fromisoformat(o["added"]) >= since]
    selected = [o for o in in_range if o["extraction"] and o["extraction"]["role_family"] == family]

    required, nice = Counter(), Counter()
    per_offer = []
    for offer in selected:
        ext = offer["extraction"]
        req = _canonicals(ext.get("skills_required"), vocab)
        required.update(req)
        nice.update(_canonicals(ext.get("skills_nice"), vocab) - req)
        backed = [c for c in req if vocab.state(c) != GAP]
        per_offer.append({
            "id": offer["id"], "company": offer["company"], "role": offer["role"],
            "coverage": len(backed) / len(req) if req else None,
        })

    skills = []
    for canonical in set(required) | set(nice):
        state = vocab.state(canonical)
        skills.append({
            "canonical": canonical, "state": state,
            "required": required[canonical], "nice": nice[canonical],
            "weight": skill_weight(required[canonical], nice[canonical], state),
            "backing": vocab.backing(canonical),
        })
    skills.sort(key=lambda s: (-s["weight"], s["canonical"].lower()))

    extractions = [o["extraction"] for o in selected]
    years = [e["years_required"] for e in extractions if e.get("years_required") is not None]
    dates = sorted(o["added"] for o in selected)
    return {
        "family": family,
        "since": since.isoformat() if since else None,
        "n_offers": len(selected),
        "weak_signal": len(selected) < MIN_OFFERS,
        "date_range": [dates[0], dates[-1]] if dates else None,
        "pending": [o["id"] for o in in_range if not o["extraction"]],
        "offers": per_offer,
        "skills": skills,
        "seniority": dict(Counter(e["seniority"] for e in extractions if e.get("seniority"))),
        "years_required_median": statistics.median(years) if years else None,
        "languages": dict(Counter(e["language"] for e in extractions if e.get("language"))),
        "languages_required": dict(Counter(
            f"{lang['language']} {lang.get('level') or ''}".strip()
            for e in extractions for lang in e.get("languages_required") or [])),
        "responsibilities": [
            {"offer_id": o["id"], "items": o["extraction"].get("responsibilities") or []}
            for o in selected
        ],
    }


def _skill_lines(report: dict, state: str) -> list[str]:
    rows = [s for s in report["skills"] if s["state"] == state]
    if not rows:
        return ["Ninguna."]
    return [
        f"- **{s['canonical']}**: requerida en {s['required']}, deseable en {s['nice']}"
        + (f" (respaldada por {', '.join(s['backing'])})" if s["backing"] else "")
        for s in rows
    ]


def _counts(counter: dict) -> str:
    return ", ".join(f"{key} ({n})" for key, n in sorted(counter.items(), key=lambda kv: -kv[1])) or "sin datos"


def render_markdown(report: dict) -> str:
    n = report["n_offers"]
    lines = [f"# Informe de mercado: {report['family']}", ""]
    period = f" entre {report['date_range'][0]} y {report['date_range'][1]}" if report["date_range"] else ""
    since = f" (desde {report['since']})" if report["since"] else ""
    lines += [f"{n} ofertas{period}{since}.", ""]
    if report["weak_signal"]:
        lines += [f"> **Señal débil:** hay menos de {MIN_OFFERS} ofertas en esta familia. "
                  "Lee las frecuencias como ejemplos, no como tendencia.", ""]
    lines += ["## Vacíos", "", "Habilidades pedidas que no aparecen en el CV.", "",
              *_skill_lines(report, GAP), ""]
    lines += ["## Mencionadas (candidatas a `tech_stack`)", "",
              "El CV las nombra, pero no están en la sección de habilidades.", "",
              *_skill_lines(report, MENTIONED), ""]
    lines += ["## Cubiertas", "", "Ya están en la sección de habilidades; conviene destacarlas.", "",
              *_skill_lines(report, COVERED), ""]
    lines += ["## Cobertura por oferta", ""]
    lines += [
        f"- {o['id']} ({o['company']}, {o['role']}): "
        + ("sin habilidades requeridas" if o["coverage"] is None else f"{o['coverage']:.0%}")
        for o in report["offers"]
    ] or ["Sin ofertas."]
    median = report["years_required_median"]
    lines += ["", "## Seniority, años e idiomas", "",
              f"- Seniority: {_counts(report['seniority'])}",
              f"- Años pedidos (mediana): {median if median is not None else 'sin datos'}",
              f"- Idioma de las ofertas: {_counts(report['languages'])}",
              f"- Idiomas requeridos: {_counts(report['languages_required'])}", ""]
    if report["pending"]:
        lines += ["## Ofertas pendientes de extracción", "",
                  "No entran en este informe. Ejecuta `make offers-extract`.", "",
                  *[f"- {offer_id}" for offer_id in report["pending"]], ""]
    return "\n".join(lines)


def write_report(report: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "report.json", out_dir / "report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path
