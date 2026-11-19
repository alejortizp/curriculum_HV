"""Helpers shared by several test files. Import with `from helpers import ...`."""

import json

import vocabulary


def vocab(cv, tmp_path, aliases=None, general_terms=None):
    """A Vocabulary for `cv` built from a throwaway vocabulary file."""
    path = tmp_path / "vocab.json"
    path.write_text(json.dumps({"aliases": aliases or {}, "general_terms": general_terms or {}}))
    return vocabulary.load(cv, path)


def fake(*responses):
    """A stand-in for llm.complete_json: returns `responses` in order and records prompts."""
    queue = list(responses)

    def complete(prompt, schema, *, model, effort, max_tokens=16000):
        complete.prompts.append(prompt)
        complete.schemas.append(schema)
        if not queue:
            raise AssertionError("el modelo fue llamado más veces de las esperadas")
        return queue.pop(0)

    complete.prompts = []
    complete.schemas = []
    return complete


GOOD = {
    "company": "Empresa Real",
    "role": "Data Engineer",
    "role_family": "data-engineer",
    "seniority": "senior",
    "language": "es",
    "languages_required": [{"language": "en", "level": "B2"}],
    "years_required": 3,
    "skills_required": [{"term": "Python", "canonical": "Python"}, {"term": "K8s", "canonical": "Kubernetes"}],
    "skills_nice": [{"term": "Snowflake", "canonical": "Snowflake"}],
    "responsibilities": ["Construir pipelines de datos."],
}


def mk(id, family, required, nice=(), added="2026-11-01", raw="texto", **extra):
    """An offer with an extraction. `required`/`nice` are skill terms; `extra` are extraction fields."""
    def skills(terms):
        return [{"term": t, "canonical": t} for t in terms]

    return {
        "id": id, "added": added, "company": "Empresa", "role": "Rol", "url": "", "status": None,
        "raw": {"text": raw, "sha256": ""},
        "extraction": {
            "schema_version": 1, "company": "Empresa", "role": "Rol", "role_family": family,
            "seniority": "senior", "language": "es", "languages_required": [{"language": "en", "level": "B2"}],
            "years_required": 3, "skills_required": skills(required), "skills_nice": skills(nice),
            "responsibilities": ["Construir pipelines."], **extra,
        },
    }


TARGET = {
    "kind": "offer", "id": "2026-11-19-globex-data-engineer", "label": "Globex - Data Engineer",
    "lang": "es", "profile": "data-engineer",
    "emphasize": ["Python"], "general_terms": {},
    "gaps": [{"canonical": "Snowflake", "forms": ["Snowflake"]}],
    "responsibilities": ["Construir pipelines."],
    "context": {"company": "Globex", "role": "Data Engineer"},
    "source_text": "Buscamos Data Engineer con Snowflake.",
}

RESP = {
    "title": "Data Engineer | Machine Learning Engineer",
    "summary": "Ingeniera de datos con pipelines en <strong>Python</strong>.",
    "experience_order": ["Acme", "Salud SA"],
    "experience": [{"company": "Acme", "bullets": ["Pipelines con Python.", "Despliegue en <strong>2 días</strong>."]}],
    "tech_stack_order": [{"category": "Datos", "first": ["Python"]}],
    "projects_shown": ["Sistema B"],
    "academic_shown": [],
    "cover_letter": {
        "recipient": "Equipo de selección", "date": "19 de noviembre de 2026",
        "subject": "Aplicación a Data Engineer", "greeting": "Hola:",
        "opening": "Me interesa el cargo de Data Engineer en Globex.",
        "why_me_title": "Por qué yo", "why_me": ["Construyo pipelines con Python."],
        "differentiator_title": "Diferencial", "differentiator": "Base en estadística.",
        "closing": "Quedo atenta.", "farewell": "Cordialmente,", "sign_off": "Ana Prueba",
    },
}
RESP_NO_LETTER = {k: v for k, v in RESP.items() if k != "cover_letter"}


def rename_company(cv_path, old, new):
    data = json.loads(cv_path.read_text(encoding="utf-8"))
    for entry in data["experience"]:
        if entry["company"] == old:
            entry["company"] = new
    cv_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def seed_offer(family, required, text="oferta de prueba"):
    import offers
    offer = offers.add(text, company="Empresa", role="Rol")
    return offers.save_extraction(offer["id"], mk("x", family, required)["extraction"])
