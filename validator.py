"""Deterministic checks on a derived CV's adjustments and cover letter (see docs/adr/0002).

validate() returns the reasons for rejection, in Spanish; an empty list means the
adjustments may be rendered. It never calls the model and never edits anything.
What it cannot see is left to the human reading the adjustments file: overstated
wording and an entry that mixes two stories.
"""

import re

from textutil import numbers, plain, term_in

# Templates render these texts unescaped, so only these exact tags may appear:
# no attributes, no other element, and no raw '<' (write it as &lt;).
_ALLOWED_TAG = re.compile(r"</?(?:strong|em)>")
_LETTER_SKIP = {"company", "role", "date"}


def entry_variants(cv: dict, company: str, lang: str) -> list[list[str]]:
    """Every hand-written version of an entry's bullets: base plus each profile's."""
    found = [exp["items"].get(lang) for exp in cv["experience"] if exp["company"] == company]
    for override in cv.get("profile_overrides", {}).values():
        found.append(override.get("experience", {}).get(company, {}).get(lang))
    return [bullets for bullets in found if bullets]


def hand_written_titles(cv: dict) -> set[str]:
    titles = [cv["personal"]["title"]] + [
        o["title"] for o in cv.get("profile_overrides", {}).values() if "title" in o]
    return {t for title in titles for t in (title.values() if isinstance(title, dict) else [title])}


def _lang_strings(value, lang: str):
    """Strings of cv.json in one language: {"es": .., "en": ..} objects yield only `lang`."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _lang_strings(item, lang)
    elif isinstance(value, dict):
        if value and set(value) <= {"es", "en"}:
            yield from _lang_strings(value.get(lang, []), lang)
        else:
            for item in value.values():
                yield from _lang_strings(item, lang)


def _title_of(project: dict, lang: str) -> str:
    title = project["title"]
    return title[lang] if isinstance(title, dict) else title


def _letter_units(letter: dict | None, lang: str, context: dict) -> list[tuple[str, str]]:
    """Text units of the letter, with the offer's own company and role removed:
    a role may carry a gap in its title and the letter has to name it."""
    exempt = [s for s in (context.get("company"), context.get("role")) if s]
    units = []
    for key, value in (letter or {}).items():
        if key in _LETTER_SKIP:
            continue
        texts = value.get(lang, "") if isinstance(value, dict) else value
        for i, text in enumerate(texts if isinstance(texts, list) else [texts], 1):
            for phrase in sorted(exempt, key=len, reverse=True):
                text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
            units.append((f"carta: {key}" + (f" {i}" if isinstance(texts, list) else ""), text))
    return units


def _rule_gaps(units, target) -> list[str]:
    return [
        f"{where}: menciona el vacío '{gap['canonical']}'"
        for where, text in units
        for gap in target.get("gaps", [])
        if any(term_in(form, plain(text)) for form in gap["forms"])
    ]


def _rule_general_terms(units, target) -> list[str]:
    return [
        f"{where}: usa '{term}' sin nombrar ninguna habilidad que lo respalde ({', '.join(backing)})"
        for where, text in units
        for term, backing in target.get("general_terms", {}).items()
        if term_in(term, plain(text)) and not any(term_in(skill, plain(text)) for skill in backing)
    ]


def _rule_markup(units) -> list[str]:
    return [
        f"{where}: solo se permiten <strong> y <em> sin atributos; un '<' suelto se escribe &lt;"
        for where, text in units
        if "<" in _ALLOWED_TAG.sub("", text)
    ]


def _letter_strings(letter: dict | None, lang: str) -> list[tuple[str, str]]:
    """Every string of the letter, including company, role and date, for the markup rule."""
    units = []
    for key, value in (letter or {}).items():
        texts = value.get(lang, "") if isinstance(value, dict) else value
        units += [(f"carta: {key}", str(text)) for text in (texts if isinstance(texts, list) else [texts])]
    return units


def _rule_figures(cv, adjustments, letter_units, lang) -> list[str]:
    reasons = []
    for company, bullets in adjustments.get("experience", {}).items():
        variants = entry_variants(cv, company, lang)
        if not variants:
            continue  # an unknown company is reported by the structure rule
        allowed = numbers(plain(" ".join(b for v in variants for b in v)))
        for i, bullet in enumerate(bullets, 1):
            extra = numbers(plain(bullet)) - allowed
            if extra:
                reasons.append(f"{company} viñeta {i}: cifras que no están en el original {sorted(extra)}")
    everywhere = numbers(plain(" ".join(_lang_strings(cv, lang))))
    for where, text in [("resumen", adjustments["summary"]), *letter_units]:
        extra = numbers(plain(text)) - everywhere
        if extra:
            reasons.append(f"{where}: cifras que no están en cv.json {sorted(extra)}")
    return reasons


def _rule_structure(cv, adjustments, lang) -> list[str]:
    reasons = []
    companies = {exp["company"] for exp in cv["experience"]}
    for company, bullets in adjustments.get("experience", {}).items():
        variants = entry_variants(cv, company, lang)
        if company not in companies or not variants:
            reasons.append(f"empresa desconocida o sin viñetas en '{lang}': {company}")
        elif len(bullets) > max(len(v) for v in variants):
            reasons.append(f"{company}: {len(bullets)} viñetas; la variante más larga tiene "
                           f"{max(len(v) for v in variants)}")

    expected = [exp["company"] for exp in cv["experience"] if lang in exp.get("langs", [lang])]
    order = adjustments.get("experience_order", [])
    if sorted(order) != sorted(expected):
        reasons.append(f"experience_order debe listar una vez cada entrada en '{lang}': "
                       f"esperadas {expected}, recibidas {order}")

    title = adjustments.get("title")
    if title and title not in hand_written_titles(cv):
        reasons.append(f"título que no fue escrito a mano: {title}")
    return reasons


def _rule_selection(cv, adjustments, lang) -> list[str]:
    reasons = []
    groups = {cat["category"]: {s["name"] for line in cat["items"] for s in line}
              for cat in cv["tech_stack"]}
    for spec in adjustments.get("tech_stack_order", []):
        if spec["category"] not in groups:
            reasons.append(f"grupo de habilidades desconocido: {spec['category']}")
            continue
        unknown = [name for name in spec.get("first", []) if name not in groups[spec["category"]]]
        if unknown:
            reasons.append(f"habilidades que no están en '{spec['category']}': {unknown}")
    for section, key in (("projects", "projects_shown"), ("academic_projects", "academic_shown")):
        known = {_title_of(p, lang) for p in cv.get(section, [])}
        unknown = [title for title in adjustments.get(key) or [] if title not in known]
        if unknown:
            reasons.append(f"{key}: proyectos desconocidos {unknown}")
    return reasons


def validate(cv: dict, adjustments: dict, target: dict,
             cover_letter: dict | None = None) -> list[str]:
    lang = adjustments["lang"]
    cv_units = [("resumen", adjustments["summary"])] + [
        (f"{company} viñeta {i}", bullet)
        for company, bullets in adjustments.get("experience", {}).items()
        for i, bullet in enumerate(bullets, 1)
    ]
    letter_units = _letter_units(cover_letter, lang, target.get("context", {}))
    units = cv_units + letter_units
    return [
        *_rule_gaps(units, target),                                # 1
        *_rule_figures(cv, adjustments, letter_units, lang),       # 2
        *_rule_structure(cv, adjustments, lang),                   # 3 and 4
        *_rule_selection(cv, adjustments, lang),                   # 5
        *_rule_general_terms(units, target),                       # 6
        *_rule_markup(cv_units + _letter_strings(cover_letter, lang)),
    ]
