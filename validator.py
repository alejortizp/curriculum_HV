"""Deterministic checks on a derived CV's adjustments and cover letter (see docs/adr/0002).

validate() returns the reasons for rejection, in Spanish; an empty list means the
adjustments may be rendered. It never calls the model and never edits anything.
What it cannot see is left to the human reading the adjustments file: overstated
wording and an entry that mixes two stories.
"""

import html
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


def _rule_summary_quotes(summary: str) -> list[str]:
    # cv.html puts `summary | striptags` in the JSON-LD block, and striptags decodes entities
    # first (&quot; becomes a quote, &lt;/script&gt; a closing tag). The template now encodes
    # that value with tojson, so this rule is a second barrier: a derived CV's summary stays
    # free of quotes, backslashes and '<' even if a template ever interpolates it raw again.
    decoded = html.unescape(_ALLOWED_TAG.sub("", summary))
    if any(char in decoded for char in '"\\<'):
        return ["resumen: no puede contener comillas dobles, barras invertidas ni '<', "
                "tampoco escritos como entidades (&quot;, &lt;)"]
    return []


def _letter_strings(letter: dict | None) -> list[tuple[str, str]]:
    """Every string of the letter, in every language and including company, role and
    date, for the markup rule: the template can print any of them."""
    units = []
    for key, value in (letter or {}).items():
        for texts in (value.values() if isinstance(value, dict) else [value]):
            units += [(f"carta: {key}", str(text)) for text in (texts if isinstance(texts, list) else [texts])]
    return units


def _rule_letter_language(letter: dict | None, lang: str) -> list[str]:
    return [f"carta: {key} no tiene texto en '{lang}'"
            for key, value in (letter or {}).items()
            if isinstance(value, dict) and lang not in value]


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _rule_shape(cv: dict, adjustments, cover_letter) -> list[str]:
    """Shape of the files, checked first: a hand-edited file must fail with a reason,
    not with a traceback halfway through the other rules."""
    if not isinstance(adjustments, dict):
        return ["los ajustes deben ser un objeto JSON"]
    reasons = []
    if adjustments.get("lang") not in ("es", "en"):
        reasons.append("lang: debe ser 'es' o 'en'")
    profile = adjustments.get("profile")
    if not isinstance(profile, str) or profile not in cv["profiles"]:
        reasons.append(f"profile: debe ser uno de {list(cv['profiles'])}")
    if not isinstance(adjustments.get("summary"), str):
        reasons.append("summary: falta o no es un texto")
    if not isinstance(adjustments.get("title"), (str, type(None))):
        reasons.append("title: debe ser un texto")
    experience = adjustments.get("experience", {})
    if not isinstance(experience, dict) or not all(_strings(bullets) for bullets in experience.values()):
        reasons.append("experience: debe tener la forma {empresa: [viñetas]}")
    for key in ("experience_order", "projects_shown", "academic_shown"):
        if not _strings(adjustments.get(key) or []):
            reasons.append(f"{key}: debe ser una lista de textos")
    order = adjustments.get("tech_stack_order", [])
    if not isinstance(order, list) or not all(
            isinstance(spec, dict) and isinstance(spec.get("category"), str)
            and _strings(spec.get("first")) for spec in order):
        reasons.append("tech_stack_order: debe ser una lista de {category, first}")
    if cover_letter is not None and not isinstance(cover_letter, dict):
        return reasons + ["la carta debe ser un objeto JSON"]
    for key, value in (cover_letter or {}).items():
        texts = list(value.values()) if isinstance(value, dict) else [value]
        if not all(isinstance(text, str) or _strings(text) for text in texts):
            reasons.append(f"carta: {key} debe ser un texto, una lista de textos o {{idioma: texto}}")
    return reasons


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


def _repeated(names: list[str]) -> list[str]:
    return sorted({name for name in names if names.count(name) > 1})


def _rule_not_empty(adjustments) -> list[str]:
    """An empty summary or a blank bullet would render an empty block."""
    reasons = []
    if not plain(adjustments["summary"]).strip():
        reasons.append("resumen: está vacío")
    for company, bullets in adjustments.get("experience", {}).items():
        if not bullets or any(not plain(bullet).strip() for bullet in bullets):
            reasons.append(f"{company}: no tiene viñetas o alguna está vacía")
    return reasons


def _rule_selection(cv, adjustments, lang) -> list[str]:
    reasons = []
    specs = adjustments.get("tech_stack_order", [])
    for label, names in [("tech_stack_order", [spec["category"] for spec in specs]),
                         *[(f"tech_stack_order {spec['category']}", spec.get("first", [])) for spec in specs],
                         ("projects_shown", adjustments.get("projects_shown") or []),
                         ("academic_shown", adjustments.get("academic_shown") or [])]:
        if _repeated(names):
            reasons.append(f"{label}: nombre repetido {_repeated(names)}")
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
    shape = _rule_shape(cv, adjustments, cover_letter)
    if shape:
        return shape
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
        *_rule_not_empty(adjustments),
        *_rule_general_terms(units, target),                       # 6
        *_rule_markup(cv_units + _letter_strings(cover_letter)),
        *_rule_letter_language(cover_letter, lang),
        *_rule_summary_quotes(adjustments["summary"]),
    ]
