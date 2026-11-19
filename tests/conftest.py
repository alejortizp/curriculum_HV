"""Shared fixtures. The `cv` fixture is hand-built so tests never depend on data/cv.json."""

import copy

import pytest

_CV = {
    "personal": {
        "name": "Ana Prueba",
        "title": "AI Engineer | Machine Learning Engineer",
        "phone": "+57 300 000 0000",
        "email": "ana@example.com",
        "location": {"es": "Bogotá, Colombia", "en": "Bogota, Colombia"},
        "links": [],
        "portfolio": {"url": "https://example.com/", "display_url": "example.com"},
    },
    "profiles": {
        "default": {"es": "Perfil general.", "en": "General profile."},
        "ml-engineer": {"es": "Perfil de ML.", "en": "ML profile."},
        "data-engineer": {
            "es": "Data Engineer con <strong>5+ años</strong> en pipelines.",
            "en": "Data Engineer with <strong>5+ years</strong> in pipelines.",
        },
    },
    "profile_overrides": {
        "data-engineer": {
            "title": "Data Engineer | Machine Learning Engineer",
            "experience": {
                "Acme": {
                    "es": ["Pipelines con Python.", "Despliegue en <strong>2 días</strong>.", "Datos sobre Delta Lake."],
                    "en": ["Pipelines with Python.", "Deployment in <strong>2 days</strong>.", "Data on Delta Lake."],
                }
            },
        }
    },
    "experience": [
        {
            "current": True,
            "langs": ["es", "en"],
            "title": {"es": "Ingeniera de IA", "en": "AI Engineer"},
            "company": "Acme",
            "start": "2023-01",
            "end": None,
            "date": {"es": "Ene 2023 – Actualidad", "en": "Jan 2023 – Present"},
            "items": {
                "es": [
                    "Extracción con <strong>95%</strong> de precisión y <strong>10k+</strong> búsquedas.",
                    "Servicio en Go (Gin) con LLMs como DeepSeek R-1.",
                ],
                "en": [
                    "Extraction with <strong>95%</strong> accuracy and <strong>10k+</strong> searches.",
                    "Service in Go (Gin) with LLMs such as DeepSeek R-1.",
                ],
            },
        },
        {
            "current": False,
            "langs": ["es"],
            "title": {"es": "Analista de Datos", "en": "Data Analyst"},
            "company": "Salud SA",
            "start": "2018-08",
            "end": "2021-04",
            "date": {"es": "Ago 2018 – Abr 2021", "en": "Aug 2018 – Apr 2021"},
            "items": {"es": ["Reportes con Pandas y SQL."]},
        },
    ],
    "projects": [
        {
            "emoji": "A",
            "title": {"es": "Agente A", "en": "Agent A"},
            "categories": ["agents"],
            "url": "https://example.com/a",
            "url_label": "example.com/a",
            "icon": "smart_toy",
            "description": {"es": "Agente de prueba.", "en": "Test agent."},
            "stack": "LangChain",
        },
        {
            "emoji": "B",
            "title": {"es": "Sistema B", "en": "System B"},
            "categories": ["classic-ml"],
            "cv": False,
            "url": "https://example.com/b",
            "url_label": "example.com/b",
            "icon": "hub",
            "description": {"es": "Sistema de prueba.", "en": "Test system."},
            "stack": "MLflow",
        },
    ],
    "academic_projects": [
        {
            "emoji": "C",
            "title": {"es": "Curso C", "en": "Course C"},
            "course": {"es": "Curso · 2026", "en": "Course · 2026"},
            "description": {"es": "Proyecto de curso.", "en": "Course project."},
            "stack": "Go",
        }
    ],
    "education": {
        "degrees": [
            {"title": {"es": "Estadística", "en": "Statistics"}, "institution": "Universidad", "date": "2011 – 2016", "current": False}
        ],
        "diplomas": [],
    },
    "tech_stack": [
        {
            "category": "Datos",
            "items": [
                [{"name": "Python", "years": 7}, {"name": "SQL", "years": 7}],
                [{"name": "Databricks + MLflow", "years": 3}],
                [{"name": "Delta Lake", "years": 1}],
                [{"name": "Go", "years": 1}],
            ],
        },
        {
            "category": "Cloud",
            "items": [[{"name": "Kubernetes", "years": 1}], [{"name": "DynamoDB", "years": 1}]],
        },
    ],
    "power_skills": {"es": ["Comunicación"], "en": ["Communication"]},
    "languages": [],
    "certifications": [],
}


@pytest.fixture
def cv():
    return copy.deepcopy(_CV)


@pytest.fixture
def offers_dir(tmp_path, monkeypatch):
    path = tmp_path / "offers"
    monkeypatch.setenv("OFFERS_DIR", str(path))
    return path
