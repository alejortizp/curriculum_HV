# Historial de ofertas y CV derivados: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Guardar ofertas de empleo, analizarlas por familia de cargo sin usar el modelo, y generar CV derivados validados a partir de `data/cv.json` sin modificarlo.

**Architecture:** Un módulo repositorio (`offers.py`) es el único que toca los archivos de ofertas. El modelo interviene en dos puntos (extracción y redacción de ajustes), siempre detrás de una función (`llm.complete_json`) que las pruebas sustituyen. Entre ambos todo es código determinista: vocabulario, informe, objetivo y validador. Los ajustes son un archivo aparte que `build.py` aplica sobre los datos base al renderizar.

**Tech Stack:** Python 3.13, `uv`, `anthropic` (Messages API con `output_config.format`), `jinja2`, `playwright` con el Chrome del sistema, `pypdf`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-11-19-historial-ofertas-design.md`. Decisiones: `docs/adr/0001-historial-de-ofertas-en-archivos-json-locales.md` y `docs/adr/0002-cv-json-inmutable-con-ajustes-validados.md`. Vocabulario: `GLOSSARY.md`.

## Global Constraints

- `data/cv.json` es de solo lectura para todo el código nuevo. Ninguna función lo escribe.
- Nada derivado de una oferta se versiona: `data/offers/` y `applications/` están en `.gitignore`.
- Solo `offers.py` lee o escribe archivos de ofertas. Ningún otro módulo construye rutas dentro de `offers_dir()`.
- Solo `llm.py` importa `anthropic`. `offers.py`, `vocabulary.py`, `report.py`, `targets.py`, `validator.py` y `textutil.py` no lo importan, ni directa ni indirectamente.
- Ninguna prueba llama a la API. Las funciones que usan el modelo reciben `complete` como parámetro con valor por defecto `llm.complete_json`.
- Dependencias de ejecución: las cuatro actuales. Única nueva de desarrollo: `pytest>=8`.
- Módulos planos en la raíz del repo, como `build.py` y `tailor.py`. Código e identificadores en inglés; mensajes al usuario en español.
- Identificador de oferta: `AAAA-MM-DD-empresa-cargo`, solo ASCII. Provisional: `AAAA-MM-DD-pendiente-<8 hex del sha256>`.
- Familias de cargo: claves de `cv["profiles"]` menos `default`, más `other`. Se leen en ejecución.
- Estados de una habilidad: `covered`, `mentioned`, `gap`.
- Aviso de señal débil del informe: menos de 10 ofertas en la familia.
- Límite del CV diseñado: 4 páginas. Superarlo es un aviso, no un error.
- En las viñetas y el resumen solo se permiten las etiquetas `<strong>` y `<em>`.
- Todo esquema enviado al modelo declara `additionalProperties: false` y lista todas sus propiedades en `required`; los valores opcionales se expresan con `anyOf` y `null`. La API no admite objetos con claves dinámicas, así que el modelo devuelve listas y el código las convierte.
- Commits en español, en imperativo, como el historial del repo. Todo el trabajo va en la rama `feature/historial-ofertas`.

## Review Focus

1. **Texto de oferta vacío o solo espacios.** Se espera un error claro y que no se cree ningún archivo. Prueba en la tarea 2.
2. **Habilidades cortas o con símbolos** (`C#`, `C++`, `.NET`, `R`, `Go`). Se espera que `Go` coincida en "Go (Gin)", que `R` no coincida en "R-1" ni en "RAG", y que `C++` no rompa la expresión regular. Prueba en la tarea 1.
3. **El modelo devuelve HTML distinto de `<strong>` y `<em>`** (un enlace, un `<script>`). Se espera rechazo del validador. Prueba en la tarea 8.
4. **`cv.json` cambió después de generar los ajustes** (empresa renombrada, proyecto eliminado). Se espera que `--render-only` falle con el motivo, no que renderice algo desactualizado. Prueba en la tarea 10.
5. **Objetivo en inglés con entradas que solo existen en español** (Savia Salud EPS tiene `langs: ["es"]`). Se espera que `experience_order` válido excluya esa entrada y que el validador no la exija. Prueba en la tarea 8.

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `textutil.py` | Texto: identificadores ASCII, quitar etiquetas, coincidencia de término completo, cifras |
| `offers.py` | Repositorio del historial de ofertas |
| `vocabulary.py` | Vocabulario, alias, términos generales y estado de una habilidad |
| `llm.py` | Única puerta a la API de Anthropic |
| `extraction.py` | Esquema, prompt y validación de la extracción |
| `report.py` | Informe de mercado por familia (JSON y Markdown) |
| `targets.py` | Construcción del objetivo desde una oferta o un informe |
| `validator.py` | Reglas deterministas sobre ajustes y carta |
| `tailor.py` | Generador unificado y render; se reescribe |
| `offers_cli.py` | Línea de comandos: `add`, `extract`, `list`, `report` |
| `build.py` | Gana `apply_adjustments()` |
| `data/skills_vocabulary.json` | Alias y términos generales; versionado |
| `tests/` | `conftest.py` y un archivo de pruebas por módulo |

---

### Task 0: Rama y documentos de diseño

**Files:**
- Create: rama `feature/historial-ofertas`

- [ ] **Step 1: Crear la rama**

```bash
git switch -c feature/historial-ofertas
```

- [ ] **Step 2: Versionar el diseño**

`data/cv.json` tiene cambios sin commit (NumPy y Azure Data Factory) que no pertenecen a esta rama: no se agregan aquí.

```bash
git add GLOSSARY.md docs/adr docs/superpowers
git commit -m "documentar el diseño del historial de ofertas y los CV derivados"
```

---

## Entrega 1: registro y extracción

### Task 1: Utilidades de texto y andamiaje de pruebas

**Files:**
- Create: `textutil.py`, `tests/conftest.py`, `tests/test_textutil.py`
- Modify: `pyproject.toml`, `Makefile`

**Interfaces:**
- Produces:
  - `slugify_ascii(text: str) -> str`
  - `plain(html: str) -> str`: quita etiquetas y convierte `&lt;`, `&gt;`, `&amp;`.
  - `term_in(term: str, text: str) -> bool`
  - `numbers(text: str) -> set[str]`
  - `tags(html: str) -> set[str]`: nombres de etiqueta en minúsculas, sin `/`.
  - Fixture `cv` en `tests/conftest.py`: un `dict` mínimo con la forma de `cv.json` (ver paso 1).
  - Fixture `offers_dir`: fija `OFFERS_DIR` a `tmp_path / "offers"` con `monkeypatch` y devuelve la ruta.
  - `tests/helpers.py`: módulo para los ayudantes que comparten varias pruebas (`vocab`, `fake`, `GOOD`, `mk`, `RESP`, `TARGET`). Cada tarea agrega ahí el suyo y las pruebas lo importan con `from helpers import ...`. `tests/` no lleva `__init__.py`.

- [ ] **Step 1: Agregar pytest y el fixture `cv`**

En `pyproject.toml`: `pytest>=8` en `[dependency-groups].dev` y

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

En `Makefile`: objetivo `test` que ejecuta `uv run pytest -q`, y su línea en `help`.

El fixture `cv` no lee `data/cv.json`. Contiene:

- `personal.title`: `"AI Engineer | Machine Learning Engineer"`; `personal.name`: `"Ana Prueba"`.
- `profiles`: `default`, `ml-engineer`, `data-engineer`, cada uno `{"es": ..., "en": ...}`; el resumen `data-engineer` en español contiene `5+ años`.
- `profile_overrides["data-engineer"]`: `title` `"Data Engineer | Machine Learning Engineer"` y, para `Acme`, 3 viñetas en `es` y 3 en `en`; una de ellas contiene `2 días`.
- `experience`: `Acme` (`langs` es y en; 2 viñetas por idioma; una en español contiene `95%` y `10k+`, y otra `Go (Gin)` y `DeepSeek R-1`) y `Salud SA` (`langs: ["es"]`, 1 viñeta que menciona `Pandas`).
- `tech_stack`: grupo `"Datos"` con líneas `[Python, SQL]`, `[Databricks + MLflow]`, `[Delta Lake]`, `[Go]`; grupo `"Cloud"` con `[Kubernetes]`, `[DynamoDB]`.
- `projects`: `"Agente A"` (sin `cv`) y `"Sistema B"` (`"cv": false`), con `title` y `description` en ambos idiomas. `academic_projects`: `"Curso C"`.

- [ ] **Step 2: Escribir las pruebas que fallan**

```python
def test_slugify_ascii_strips_accents_and_enie():
    assert slugify_ascii("Compañía Ñandú  S.A.S") == "compania-nandu-sas"

def test_slugify_ascii_of_symbols_only_is_empty():
    assert slugify_ascii("—🚀—") == ""

def test_plain_removes_tags_and_entities():
    assert plain("<strong>a</strong> &lt;200ms &amp; b") == "a <200ms & b"

@pytest.mark.parametrize("term,text,expected", [
    ("Go", "servicio en Go (Gin)", True),
    ("R", "LLMs como DeepSeek R-1", False),
    ("R", "agente RAG", False),
    ("C++", "motor en C++ y Rust", True),
    ("C#", "API en C#.", True),
    (".NET", "backend .NET 8", True),
    ("kubernetes", "desplegado en Kubernetes (EKS)", True),
    ("Lake", "sobre Delta Lake", True),
    ("Spark", "con PySpark", False),
])
def test_term_in(term, text, expected):
    assert term_in(term, text) is expected

def test_tags():
    assert tags('<strong>a</strong> <a href="x">b</a> <EM>c</EM>') == {"strong", "a", "em"}
```

- [ ] **Step 3: Verificar que fallan**

Run: `uv run pytest tests/test_textutil.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'textutil'`

- [ ] **Step 4: Implementar `textutil.py`, salvo `numbers`**

`term_in`: el término escapado con `re.escape`, sin distinguir mayúsculas, y sin una letra, un dígito o un guion pegados a ningún lado. `slugify_ascii`: `unicodedata.normalize("NFKD")`, descartar lo no ASCII, y después las mismas sustituciones de `slugify()` en `tailor.py:47-53`.

- [ ] **Step 5: `numbers()` — contribución de Alejandro**

Dejar preparado en `textutil.py`:

```python
def numbers(text: str) -> set[str]:
    """Cifras de un texto, en la forma en que el validador las compara.

    El validador rechaza una viñeta si numbers(viñeta) no es subconjunto de
    numbers(original). Esta función decide qué tan estricta es esa regla.
    """
    # TODO(Alejandro): 5-10 líneas.
    raise NotImplementedError
```

Y estas pruebas, que fijan solo lo que no admite discusión:

```python
def test_numbers_finds_plain_integers():
    assert {"95", "500"} <= numbers("95% de precisión, 500 CVs")

def test_numbers_ignores_text_without_digits():
    assert numbers("sin cifras") == set()
```

La decisión que le corresponde: si `10k+`, `<200ms`, `60–70%`, `0.87` y `2 días` se comparan como dígitos sueltos (`10`, `200`, `60`, `70`, `0`, `87`, `2`) o como fichas con su unidad (`10k`, `200ms`, `0.87`). Dígitos sueltos acepta que el modelo cambie `10k` por `10`; fichas con unidad rechaza reformulaciones inocentes como `200 ms`. Debe agregar una prueba por cada caso que decida.

- [ ] **Step 6: Verificar que pasan**

Run: `uv run pytest tests/test_textutil.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add textutil.py tests pyproject.toml uv.lock Makefile
git commit -m "agregar utilidades de texto y pruebas con pytest"
```

### Task 2: Repositorio del historial de ofertas

**Files:**
- Create: `offers.py`, `tests/test_offers.py`

**Interfaces:**
- Consumes: `textutil.slugify_ascii`; fixture `offers_dir`.
- Produces:
  - `offers_dir() -> Path`: `OFFERS_DIR` del entorno, si no de `.env`, si no `ROOT / "data" / "offers"`.
  - `add(raw_text: str, *, company: str = "", role: str = "", url: str = "", today: date | None = None) -> dict`
  - `get(offer_id: str) -> dict`
  - `list_offers(*, family: str | None = None, since: date | None = None) -> list[dict]`: ordenadas por `added` y luego `id`.
  - `save_extraction(offer_id: str, extraction: dict) -> dict`: devuelve la oferta, con el identificador definitivo si lo asignó.
  - Excepciones `OfferNotFound`, `DuplicateOffer` (atributo `existing_id`), `EmptyOffer`.
  - Forma de una oferta: la del spec, sección "Historial de ofertas". `extraction` contiene además `company` y `role` tal como los identificó el modelo.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
D = date(2026, 11, 19)

def test_add_with_company_and_role_assigns_final_id(offers_dir):
    offer = offers.add("texto", company="Acme", role="ML Engineer", today=D)
    assert offer["id"] == "2026-11-19-acme-ml-engineer"
    assert offer["extraction"] is None and offer["status"] is None
    assert (offers_dir / "2026-11-19-acme-ml-engineer.json").exists()

def test_add_without_company_uses_provisional_id(offers_dir):
    offer = offers.add("texto", today=D)
    assert re.fullmatch(r"2026-11-19-pendiente-[0-9a-f]{8}", offer["id"])

def test_same_company_and_role_same_day_gets_suffix(offers_dir):
    offers.add("uno", company="Acme", role="ML Engineer", today=D)
    assert offers.add("dos", company="Acme", role="ML Engineer", today=D)["id"].endswith("-2")

def test_duplicate_text_is_rejected(offers_dir):
    first = offers.add("texto", company="Acme", role="X", today=D)
    with pytest.raises(offers.DuplicateOffer) as exc:
        offers.add("texto", company="Otra", role="Y", today=D)
    assert exc.value.existing_id == first["id"]

@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_empty_text_is_rejected_and_writes_nothing(offers_dir, text):
    with pytest.raises(offers.EmptyOffer):
        offers.add(text, today=D)
    assert not offers_dir.exists() or not list(offers_dir.iterdir())

def test_unsluggable_company_falls_back_to_provisional_id(offers_dir):
    assert "-pendiente-" in offers.add("texto", company="—", role="🚀", today=D)["id"]

def test_first_extraction_finalizes_provisional_id_once(offers_dir):
    old = offers.add("texto", today=D)["id"]
    offer = offers.save_extraction(old, {"company": "Acme", "role": "Data Engineer", "role_family": "data-engineer"})
    assert offer["id"] == "2026-11-19-acme-data-engineer"
    assert offer["company"] == "Acme" and not (offers_dir / f"{old}.json").exists()
    again = offers.save_extraction(offer["id"], {"company": "Otra", "role": "Z", "role_family": "other"})
    assert again["id"] == offer["id"] and again["company"] == "Acme"

def test_extraction_never_rewrites_raw(offers_dir):
    offer = offers.add("texto original", company="Acme", role="X", today=D)
    offers.save_extraction(offer["id"], {"company": "A", "role": "B", "role_family": "other"})
    assert offers.get(offer["id"])["raw"] == offer["raw"]

def test_list_filters_by_family_and_date(offers_dir):
    a = offers.add("a", company="A", role="X", today=date(2026, 1, 1))
    b = offers.add("b", company="B", role="X", today=date(2026, 6, 1))
    offers.save_extraction(a["id"], {"company": "A", "role": "X", "role_family": "mlops"})
    offers.save_extraction(b["id"], {"company": "B", "role": "X", "role_family": "mlops"})
    assert [o["id"] for o in offers.list_offers(family="mlops", since=date(2026, 3, 1))] == [b["id"]]
    assert offers.list_offers(family="data-engineer") == []

def test_get_unknown_offer(offers_dir):
    with pytest.raises(offers.OfferNotFound):
        offers.get("no-existe")
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_offers.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'offers'`

- [ ] **Step 3: Implementar `offers.py`**

El duplicado se detecta comparando el `sha256` del texto sin espacios al inicio ni al final contra el de cada oferta existente. `save_extraction` solo rellena `company` y `role` del nivel superior cuando están vacíos, y solo renombra cuando el identificador actual contiene `-pendiente-`. Los archivos se escriben con `ensure_ascii=False` e `indent=2`.

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_offers.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add offers.py tests/test_offers.py
git commit -m "agregar el repositorio del historial de ofertas"
```

### Task 3: Vocabulario, alias y términos generales

**Files:**
- Create: `vocabulary.py`, `data/skills_vocabulary.json`, `tests/test_vocabulary.py`

**Interfaces:**
- Consumes: `textutil.term_in`, `textutil.plain`; fixture `cv`.
- Produces:
  - `VOCAB_FILE = ROOT / "data" / "skills_vocabulary.json"`
  - `load(cv: dict, path: Path = VOCAB_FILE) -> Vocabulary`; lanza `VocabularyError`.
  - `Vocabulary.names: list[str]`: nombres de `tech_stack`, en orden.
  - `Vocabulary.canonical(term: str, model_canonical: str | None = None) -> str`
  - `Vocabulary.state(canonical: str) -> str`: `"covered"`, `"mentioned"` o `"gap"`.
  - `Vocabulary.backing(canonical: str) -> list[str]`: habilidades que respaldan un término general; lista vacía si no lo es.
  - `Vocabulary.forms(canonical: str) -> list[str]`: el canónico más todos los alias que apuntan a él.
  - `Vocabulary.general_terms: dict[str, list[str]]`

- [ ] **Step 1: Escribir las pruebas que fallan**

Las pruebas escriben su propio archivo de vocabulario en `tmp_path` con un ayudante `vocab(cv, tmp_path, aliases={}, general_terms={})`.

```python
def test_names_come_from_tech_stack(cv, tmp_path):
    assert vocab(cv, tmp_path).names == ["Python", "SQL", "Databricks + MLflow", "Delta Lake", "Go", "Kubernetes", "DynamoDB"]

def test_alias_file_wins_over_model_canonical(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"K8s": "Kubernetes"})
    assert v.canonical("k8s", "Docker") == "Kubernetes"

def test_canonical_uses_vocabulary_casing(cv, tmp_path):
    assert vocab(cv, tmp_path).canonical("PYTHON") == "Python"

def test_unknown_term_keeps_model_canonical(cv, tmp_path):
    assert vocab(cv, tmp_path).canonical("DBT Core", "dbt") == "dbt"

def test_three_states(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"MLflow": "Databricks + MLflow"})
    assert v.state("Python") == "covered"
    assert v.state(v.canonical("MLflow")) == "covered"
    assert v.state("Pandas") == "mentioned"      # solo en una viñeta
    assert v.state("Snowflake") == "gap"
    assert v.state("R") == "gap"                 # "DeepSeek R-1" no cuenta

def test_alias_form_counts_as_mention(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"Gin": "Gin Web Framework"})
    assert v.state("Gin Web Framework") == "mentioned"   # el CV dice "Gin", no el canónico

def test_general_term_inherits_best_state(cv, tmp_path):
    v = vocab(cv, tmp_path, general_terms={"Lakehouse": ["Delta Lake"], "Dataframes": ["Pandas"]})
    assert v.state("Lakehouse") == "covered" and v.backing("Lakehouse") == ["Delta Lake"]
    assert v.state("Dataframes") == "mentioned"

def test_general_term_backed_by_gap_fails(cv, tmp_path):
    with pytest.raises(VocabularyError, match="Snowflake"):
        vocab(cv, tmp_path, general_terms={"Data Warehouse": ["Snowflake"]})

def test_forms(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"K8s": "Kubernetes", "kube": "Kubernetes"})
    assert set(v.forms("Kubernetes")) == {"Kubernetes", "K8s", "kube"}

def test_missing_file_means_no_aliases(cv, tmp_path):
    assert vocabulary.load(cv, tmp_path / "no.json").state("Python") == "covered"

def test_real_files_load():
    vocabulary.load(build.load_json(build.DATA_FILE))
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_vocabulary.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'vocabulary'`

- [ ] **Step 3: Implementar `vocabulary.py`**

El texto del CV es la concatenación de todos los valores de tipo cadena de `cv`, recorridos recursivamente y pasados por `plain`. Una habilidad es `mentioned` si alguna de sus `forms` cumple `term_in` contra ese texto. Las claves de alias se comparan en minúsculas.

- [ ] **Step 4: Crear `data/skills_vocabulary.json`**

```json
{
  "aliases": {
    "K8s": "Kubernetes",
    "Databricks": "Databricks + MLflow",
    "MLflow": "Databricks + MLflow",
    "Scikit-Learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "Azure Document Intelligence": "Document Intelligence",
    "Microsoft Azure": "Azure",
    "Data Pipeline": "Data Pipelines",
    "ADF": "Azure Data Factory"
  },
  "general_terms": {
    "Lakehouse": ["Delta Lake", "Unity Catalog"],
    "NoSQL": ["DynamoDB"],
    "Bases de datos relacionales": ["Cloud SQL", "RDS"]
  }
}
```

Los tres términos generales son los que quedaron abiertos el 2026-11-19; Alejandro confirma o quita cada uno antes del commit.

- [ ] **Step 5: Verificar que pasan**

Run: `uv run pytest tests/test_vocabulary.py -q`
Expected: PASS, incluida `test_real_files_load`

- [ ] **Step 6: Commit**

```bash
git add vocabulary.py data/skills_vocabulary.json tests/test_vocabulary.py
git commit -m "agregar el vocabulario de habilidades con alias y términos generales"
```

### Task 4: Puerta a la API y extracción

**Files:**
- Create: `llm.py`, `extraction.py`, `tests/test_extraction.py`
- Modify: `pyproject.toml` (versión mínima de `anthropic`)

**Interfaces:**
- Consumes: `vocabulary.Vocabulary`.
- Produces:
  - `llm.complete_json(prompt: str, schema: dict, *, model: str, effort: str, max_tokens: int = 16000) -> dict`
  - `llm.LLMError`
  - `llm.EXTRACTION_MODEL = "claude-opus-5-5"`, `llm.EXTRACTION_EFFORT = "low"`, `llm.TAILORING_MODEL = "claude-opus-5-5"`, `llm.TAILORING_EFFORT = "high"`
  - `extraction.SCHEMA_VERSION = 1`
  - `extraction.role_families(cv: dict) -> list[str]`
  - `extraction.extract(raw_text: str, cv: dict, vocab: Vocabulary, complete=llm.complete_json) -> dict`; lanza `ExtractionError`.

- [ ] **Step 1: Escribir las pruebas que fallan**

`fake(*responses)` devuelve un `complete` que entrega las respuestas en orden y guarda cada `prompt` en `fake.prompts`. `GOOD` es una respuesta válida con `role_family: "data-engineer"`.

```python
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
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_extraction.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `llm.py`**

La forma de la llamada no se deduce de la firma, así que va completa:

```python
def complete_json(prompt, schema, *, model, effort, max_tokens=16000):
    try:
        response = _client().beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError as e:
        raise LLMError("Credenciales de Anthropic inválidas o ausentes.") from e
    except anthropic.RateLimitError as e:
        raise LLMError("Límite de uso alcanzado; intenta de nuevo en unos minutos.") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"Error de la API ({e.status_code}): {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError("Sin conexión con la API de Anthropic.") from e
    if response.stop_reason == "refusal":
        raise LLMError("El modelo rechazó la solicitud.")
    if response.stop_reason == "max_tokens":
        raise LLMError("La respuesta se cortó por max_tokens.")
    return json.loads(next(b.text for b in response.content if b.type == "text"))
```

`_client()` crea `anthropic.Anthropic()` una sola vez. Antes, si `ANTHROPIC_API_KEY` no está en el entorno y `.env` la define, la copia a `os.environ`; es la lógica de `get_anthropic_key()` en `tailor.py:30-44`, sin el `sys.exit`. No se envían `thinking`, `temperature` ni `tool_choice`: `claude-opus-5-5` los rechaza o los ignora.

- [ ] **Step 4: Implementar `extraction.py`**

Campos de la respuesta del modelo: `company`, `role`, `role_family` (enumeración de `role_families(cv)`), `seniority` (`junior`, `mid`, `senior`, `lead` o `null`), `language` (`es`, `en`, `other`), `languages_required` (lista de `{language, level}` con `level` cadena o `null`), `years_required` (entero o `null`), `skills_required` y `skills_nice` (listas de `{term, canonical}`), `responsibilities` (lista de cadenas).

El prompt indica: solo habilidades técnicas; `canonical` es un nombre de la lista del vocabulario cuando corresponde y, si no, el nombre corto habitual de la tecnología; nunca vacío. `validate_extraction(data, families) -> list[str]` devuelve motivos; con motivos, se reintenta una vez agregándolos al prompt.

- [ ] **Step 5: Verificar que pasan**

Run: `uv run pytest tests/test_extraction.py -q`
Expected: PASS

- [ ] **Step 6: Prueba real contra la API (una llamada, cuesta centavos)**

Requiere el visto bueno de Alejandro porque gasta saldo.

Run: `uv run python -c "import llm; print(llm.complete_json('Responde con ok=true.', {'type':'object','properties':{'ok':{'type':'boolean'}},'required':['ok'],'additionalProperties':False}, model=llm.EXTRACTION_MODEL, effort='low', max_tokens=1024))"`
Expected: `{'ok': True}`

Si falla con `TypeError` por `output_config` o `fallbacks`, la versión instalada de `anthropic` (0.84.0) es anterior a esos parámetros: ejecutar `uv lock --upgrade-package anthropic && uv sync`, repetir, y fijar en `pyproject.toml` como mínimo la versión que resulte.

- [ ] **Step 7: Commit**

```bash
git add llm.py extraction.py tests/test_extraction.py pyproject.toml uv.lock
git commit -m "agregar la extracción estructurada de ofertas con el modelo"
```

### Task 5: Comandos de registro

**Files:**
- Create: `offers_cli.py`, `tests/test_offers_cli.py`
- Modify: `Makefile`, `.gitignore`
- Delete: `data/job_offer_template.json`

**Interfaces:**
- Consumes: `offers.*`, `extraction.extract`, `vocabulary.load`.
- Produces:
  - `offers_cli.cmd_add(text: str, *, company="", role="", url="", complete=llm.complete_json) -> dict`
  - `offers_cli.cmd_extract(*, force: bool = False, complete=llm.complete_json) -> list[dict]`
  - `offers_cli.cmd_list() -> list[dict]`
  - `python offers_cli.py add [--file F] [--company C] [--role R] [--url U]` (sin `--file` lee la entrada estándar), `extract [--force]`, `list`.
  - Make: `offer-add FILE= COMPANY= ROLE= URL=`, `offers-extract FORCE=1`, `offers-list`.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
def test_add_saves_raw_before_extracting(offers_dir, cv_file):
    def boom(*a, **k): raise llm.LLMError("sin red")
    with pytest.raises(llm.LLMError):
        offers_cli.cmd_add("texto de oferta", complete=boom)
    [pending] = offers.list_offers()
    assert pending["extraction"] is None and "-pendiente-" in pending["id"]

def test_add_extracts_and_finalizes_id(offers_dir, cv_file):
    offer = offers_cli.cmd_add("texto", complete=fake(GOOD))
    assert "-pendiente-" not in offer["id"] and offer["extraction"]["role_family"] == "data-engineer"

def test_company_parameter_wins_over_model(offers_dir, cv_file):
    assert offers_cli.cmd_add("texto", company="Mía", role="Rol", complete=fake(GOOD))["company"] == "Mía"

def test_extract_only_touches_pending_unless_forced(offers_dir, cv_file):
    offers_cli.cmd_add("uno", complete=fake(GOOD))
    assert offers_cli.cmd_extract(complete=fake()) == []
    assert len(offers_cli.cmd_extract(force=True, complete=fake(GOOD))) == 1
```

`cv_file` es un fixture de `tests/conftest.py` que apunta `build.DATA_FILE` y `vocabulary.VOCAB_FILE` a copias en `tmp_path` del fixture `cv`, y devuelve la ruta del CV. Para que funcione, todo comando carga el CV con `build.load_json(build.DATA_FILE)` en el momento de ejecutarse, nunca en una constante de módulo.

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_offers_cli.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `offers_cli.py` y los objetivos de `Makefile`**

`DuplicateOffer`, `EmptyOffer` y `LLMError` se muestran como una línea en español y terminan con código 1, sin traza. Tras `add`, se imprimen identificador, empresa, cargo y familia.

- [ ] **Step 4: Actualizar `.gitignore` y retirar la plantilla**

Reemplazar la línea `data/job_offer.json` y su comentario por `data/offers/` con el comentario `# Historial de ofertas (privado; ver ADR-0001)`. Borrar `data/job_offer_template.json`.

- [ ] **Step 5: Verificar**

Run: `uv run pytest -q && git check-ignore -q data/offers/x.json && echo ignorado`
Expected: PASS e `ignorado`

- [ ] **Step 6: Commit**

```bash
git add offers_cli.py tests/test_offers_cli.py Makefile .gitignore
git rm -q data/job_offer_template.json
git commit -m "agregar los comandos para registrar y extraer ofertas"
```

---

## Entrega 2: informe de mercado

### Task 6: Informe por familia

**Files:**
- Create: `report.py`, `tests/test_report.py`
- Modify: `offers_cli.py`, `Makefile`

**Interfaces:**
- Consumes: `offers.list_offers`, `vocabulary.Vocabulary`.
- Produces:
  - `MIN_OFFERS = 10`
  - `skill_weight(required: int, nice: int, state: str) -> float`
  - `build_report(offers: list[dict], family: str, vocab: Vocabulary, since: date | None = None) -> dict`
  - `render_markdown(report: dict) -> str`
  - `write_report(report: dict, out_dir: Path) -> tuple[Path, Path]`: `report.json` y `report.md`.
  - `offers_cli.cmd_report(family: str | None = None, since: date | None = None) -> list[Path]`; Make `offers-report FAMILY= SINCE=`. Salida en `applications/_market/<familia>/`.
  - Forma del informe:

```python
{
  "family": str, "since": str | None, "n_offers": int, "weak_signal": bool,
  "date_range": [str, str] | None,
  "pending": [str],                       # ids sin extracción, excluidos
  "offers": [{"id", "company", "role", "coverage": float | None}],
  "skills": [{"canonical", "state", "required": int, "nice": int,
              "weight": float, "backing": [str]}],   # orden: weight desc, canonical
  "seniority": {str: int}, "years_required_median": float | None,
  "languages": {str: int}, "languages_required": {str: int},   # clave "en B2"
  "responsibilities": [{"offer_id": str, "items": [str]}],
}
```

- [ ] **Step 1: Escribir las pruebas que fallan**

`mk(id, family, required, nice=(), added="2026-11-01", raw="texto", **extra)` construye una oferta con extracción: `required` y `nice` son listas de términos (el `canonical` del modelo es el mismo término), `raw` es el texto crudo y `extra` son campos adicionales de la extracción, como `language="en"`.

```python
def test_counts_required_and_nice_per_offer(cv, tmp_path):
    r = build_report([mk("a", "data-engineer", ["Python", "K8s"]), mk("b", "data-engineer", ["python"], nice=["Snowflake"])],
                     "data-engineer", vocab(cv, tmp_path, aliases={"K8s": "Kubernetes"}))
    by = {s["canonical"]: s for s in r["skills"]}
    assert (by["Python"]["required"], by["Python"]["state"]) == (2, "covered")
    assert by["Kubernetes"]["required"] == 1
    assert (by["Snowflake"]["nice"], by["Snowflake"]["state"]) == (1, "gap")

def test_same_skill_twice_in_one_offer_counts_once(cv, tmp_path):
    r = build_report([mk("a", "data-engineer", ["Python", "python"])], "data-engineer", vocab(cv, tmp_path))
    assert r["skills"][0]["required"] == 1

def test_coverage_is_share_of_required_that_are_not_gaps(cv, tmp_path):
    r = build_report([mk("a", "data-engineer", ["Python", "Pandas", "Snowflake", "dbt"])], "data-engineer", vocab(cv, tmp_path))
    assert r["offers"][0]["coverage"] == 0.5

def test_offer_without_required_skills_has_no_coverage(cv, tmp_path):
    assert build_report([mk("a", "data-engineer", [])], "data-engineer", vocab(cv, tmp_path))["offers"][0]["coverage"] is None

def test_other_families_and_pending_are_excluded(cv, tmp_path):
    pending = {"id": "p", "added": "2026-11-01", "extraction": None}
    r = build_report([mk("a", "data-engineer", ["Python"]), mk("b", "mlops", ["Go"]), pending], "data-engineer", vocab(cv, tmp_path))
    assert r["n_offers"] == 1 and r["pending"] == ["p"]

def test_since_filters_by_added(cv, tmp_path):
    r = build_report([mk("a", "data-engineer", ["Python"], added="2026-01-01"), mk("b", "data-engineer", ["Go"], added="2026-06-01")],
                     "data-engineer", vocab(cv, tmp_path), since=date(2026, 3, 1))
    assert [o["id"] for o in r["offers"]] == ["b"]

def test_weak_signal_below_ten_offers(cv, tmp_path):
    nine = [mk(f"o{i}", "data-engineer", ["Python"]) for i in range(9)]
    assert build_report(nine, "data-engineer", vocab(cv, tmp_path))["weak_signal"] is True
    assert build_report(nine + [mk("o9", "data-engineer", ["Go"])], "data-engineer", vocab(cv, tmp_path))["weak_signal"] is False

def test_general_term_shows_backing(cv, tmp_path):
    r = build_report([mk("a", "data-engineer", ["Lakehouse"])], "data-engineer", vocab(cv, tmp_path, general_terms={"Lakehouse": ["Delta Lake"]}))
    assert r["skills"][0]["backing"] == ["Delta Lake"] and r["skills"][0]["state"] == "covered"

def test_markdown_lists_gaps_and_warns(cv, tmp_path):
    md = render_markdown(build_report([mk("a", "data-engineer", ["Snowflake"])], "data-engineer", vocab(cv, tmp_path)))
    assert "Snowflake" in md and "señal débil" in md.lower()

def test_empty_family_report(cv, tmp_path):
    r = build_report([], "data-engineer", vocab(cv, tmp_path))
    assert r["n_offers"] == 0 and r["skills"] == [] and r["date_range"] is None
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_report.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `report.py`, salvo `skill_weight`**

`render_markdown` tiene estas secciones, en este orden: encabezado con familia, número de ofertas y rango de fechas; aviso de señal débil si aplica; "Vacíos"; "Mencionadas (candidatas a `tech_stack`)"; "Cubiertas"; "Cobertura por oferta"; "Seniority, años e idiomas"; "Ofertas pendientes de extracción" si las hay.

- [ ] **Step 4: `skill_weight()` — contribución de Alejandro**

Dejar preparado en `report.py`:

```python
def skill_weight(required: int, nice: int, state: str) -> float:
    """Peso con que una habilidad se ordena en el informe y en el objetivo.

    required/nice: en cuántas ofertas de la familia aparece como requerida o deseable.
    state: "covered", "mentioned" o "gap".
    Mayor peso = más arriba en el informe y más prioridad para destacarla en el CV.
    """
    # TODO(Alejandro): 5-10 líneas.
    raise NotImplementedError
```

Y esta prueba, que fija solo lo indiscutible:

```python
def test_weight_grows_with_required_count():
    assert skill_weight(3, 0, "covered") > skill_weight(1, 0, "covered")
```

Lo que le corresponde decidir: cuánto vale una mención como deseable frente a una como requerida, y si el estado altera el peso. Si `covered` pesa más que `mentioned`, el CV derivado destaca primero lo que ya está en la sección de habilidades; si pesan igual, manda solo la demanda del mercado. Debe agregar una prueba por cada regla que decida.

- [ ] **Step 5: Agregar `cmd_report` y el objetivo `offers-report`**

Sin `--family`, un informe por cada familia con al menos una oferta extraída.

- [ ] **Step 6: Verificar que pasan**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add report.py offers_cli.py tests/test_report.py Makefile
git commit -m "agregar el informe de mercado por familia de cargo"
```

---

## Entrega 3: generador unificado

### Task 7: Aplicar ajustes sobre los datos del CV

**Files:**
- Modify: `build.py` (junto a `apply_profile_overrides`, línea 205)
- Create: `tests/test_apply_adjustments.py`

**Interfaces:**
- Produces: `build.apply_adjustments(cv_data: dict, adjustments: dict) -> dict`. Devuelve datos nuevos con `profile` igual a `{lang: summary}`; no modifica `cv_data`. Lanza `ValueError` con el nombre desconocido.
- Forma de los ajustes: la del spec, sección "Ajustes". `title`, `tech_stack_order`, `projects_shown` y `academic_shown` son opcionales.

- [ ] **Step 1: Escribir las pruebas que fallan**

`ADJ` es un ajuste mínimo válido para el fixture `cv`: `lang: "es"`, `summary`, `experience_order: ["Salud SA", "Acme"]`, `experience: {"Acme": ["nueva"]}`.

```python
def test_does_not_mutate_input(cv):
    before = copy.deepcopy(cv)
    build.apply_adjustments(cv, ADJ)
    assert cv == before

def test_summary_title_order_and_bullets(cv):
    out = build.apply_adjustments(cv, {**ADJ, "title": "Data Engineer | Machine Learning Engineer"})
    assert out["profile"] == {"es": ADJ["summary"]}
    assert out["personal"]["title"] == "Data Engineer | Machine Learning Engineer"
    assert [e["company"] for e in out["experience"]] == ["Salud SA", "Acme"]
    assert out["experience"][1]["items"]["es"] == ["nueva"]
    assert out["experience"][1]["items"]["en"] == cv["experience"][0]["items"]["en"]

def test_entry_missing_from_order_keeps_position_at_end(cv):
    out = build.apply_adjustments(cv, {**ADJ, "experience_order": ["Salud SA"]})
    assert [e["company"] for e in out["experience"]] == ["Salud SA", "Acme"]

def test_tech_stack_order_reorders_without_changing_the_set(cv):
    out = build.apply_adjustments(cv, {**ADJ, "tech_stack_order": [{"category": "Cloud", "first": ["DynamoDB"]}, {"category": "Datos", "first": ["Go", "Delta Lake"]}]})
    assert [c["category"] for c in out["tech_stack"]] == ["Cloud", "Datos"]
    assert [line[0]["name"] for line in out["tech_stack"][0]["items"]] == ["DynamoDB", "Kubernetes"]
    assert [line[0]["name"] for line in out["tech_stack"][1]["items"]] == ["Go", "Delta Lake", "Python", "Databricks + MLflow"]

def test_projects_shown_can_reveal_a_hidden_project(cv):
    out = build.apply_adjustments(cv, {**ADJ, "projects_shown": ["Sistema B"]})
    assert [(p["title"]["es"], p["cv"]) for p in out["projects"]] == [("Sistema B", True), ("Agente A", False)]

def test_without_projects_shown_cv_flags_are_kept(cv):
    assert build.apply_adjustments(cv, ADJ)["projects"] == cv["projects"]

@pytest.mark.parametrize("patch,name", [
    ({"experience": {"Nadie": ["x"]}}, "Nadie"),
    ({"tech_stack_order": [{"category": "Nube", "first": []}]}, "Nube"),
    ({"projects_shown": ["Fantasma"]}, "Fantasma"),
    ({"academic_shown": ["Fantasma"]}, "Fantasma"),
])
def test_unknown_names_raise(cv, patch, name):
    with pytest.raises(ValueError, match=name):
        build.apply_adjustments(cv, {**ADJ, **patch})
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_apply_adjustments.py -q`
Expected: FAIL con `AttributeError: module 'build' has no attribute 'apply_adjustments'`

- [ ] **Step 3: Implementar `apply_adjustments`**

Los títulos de proyectos se comparan en el idioma de los ajustes. El orden de líneas dentro de un grupo usa la primera habilidad de cada línea, como hizo la corrida manual del 2026-11-19.

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_apply_adjustments.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add build.py tests/test_apply_adjustments.py
git commit -m "agregar la aplicación de ajustes sobre los datos del CV"
```

### Task 8: Validador

**Files:**
- Create: `validator.py`, `tests/test_validator.py`

**Interfaces:**
- Consumes: `textutil.{plain, term_in, numbers, tags}`; `vocabulary.Vocabulary` vía el objetivo.
- Produces:
  - `entry_variants(cv: dict, company: str, lang: str) -> list[list[str]]`: viñetas base más las de cada perfil en `profile_overrides`.
  - `hand_written_titles(cv: dict) -> set[str]`
  - `validate(cv: dict, adjustments: dict, target: dict, cover_letter: dict | None = None) -> list[str]`: motivos en español; lista vacía si pasa.
  - Del objetivo solo lee `gaps` (lista de `{"canonical": str, "forms": [str]}`), `general_terms` (`{término: [habilidades]}`) y `context` (`company`, `role`).

- [ ] **Step 1: Escribir las pruebas que fallan**

`OK` es un ajuste válido para el fixture `cv` en español, con un resumen sin cifras; `T` un objetivo con `gaps: [{"canonical": "Snowflake", "forms": ["Snowflake", "SnowSQL"]}]`, `general_terms: {"Lakehouse": ["Delta Lake"]}` y `context: {"company": "Snowflake Inc", "role": "Snowflake Data Engineer"}`. `bad(**patch)` devuelve `validate(cv, {**OK, **patch}, T)`.

```python
def test_valid_adjustments_pass(cv):
    assert validate(cv, OK, T) == []

def test_variants_include_profile_overrides(cv):
    assert len(entry_variants(cv, "Acme", "es")) == 2
    assert len(entry_variants(cv, "Salud SA", "es")) == 1

# Regla 1
def test_gap_term_or_alias_is_rejected(cv):
    assert any("Snowflake" in r for r in bad(summary="Experto en snowflake."))
    assert any("Snowflake" in r for r in bad(experience={"Acme": ["Consultas con SnowSQL."]}))

def test_company_and_role_are_exempt_in_the_letter_only(cv):
    letter = {"opening": {"es": "Me postulo a Snowflake Data Engineer en Snowflake Inc."}}
    assert validate(cv, OK, T, letter) == []
    assert validate(cv, OK, T, {"opening": {"es": "Domino Snowflake."}}) != []

# Regla 2
def test_figure_from_another_variant_of_the_same_entry_is_allowed(cv):
    assert bad(experience={"Acme": ["Despliegue en 2 días."]}) == []

def test_figure_outside_the_entry_is_rejected(cv):
    assert any("Acme" in r for r in bad(experience={"Acme": ["Mejora del 99%."]}))

def test_summary_figure_must_exist_in_cv_text(cv):
    assert bad(summary="Con 5+ años.") == []
    assert bad(summary="Con 12+ años.") != []

# Regla 3
def test_more_bullets_than_longest_variant_is_rejected(cv):
    assert bad(experience={"Acme": ["a", "b", "c"]}) == []
    assert bad(experience={"Acme": ["a", "b", "c", "d"]}) != []

# Regla 4
def test_unknown_company_and_title(cv):
    assert any("Nadie" in r for r in bad(experience={"Nadie": ["a"]}))
    assert bad(title="Data Engineer | Machine Learning Engineer") == []
    assert bad(title="Chief Everything Officer") != []

def test_order_must_list_every_entry_in_that_language(cv):
    assert bad(experience_order=["Acme"]) != []
    en = {**OK, "lang": "en", "experience_order": ["Acme"], "experience": {}}
    assert validate(cv, en, T) == []          # Salud SA solo existe en español

# Regla 5
def test_unknown_group_skill_or_project(cv):
    assert bad(tech_stack_order=[{"category": "Nube", "first": []}]) != []
    assert bad(tech_stack_order=[{"category": "Datos", "first": ["Rust"]}]) != []
    assert bad(projects_shown=["Fantasma"]) != []

# Regla 6
def test_general_term_needs_a_backing_skill_in_the_same_text(cv):
    assert bad(summary="Arquitectura Lakehouse sobre Delta Lake.") == []
    assert any("Lakehouse" in r for r in bad(summary="Arquitectura Lakehouse."))

# Etiquetas
def test_only_strong_and_em_are_allowed(cv):
    assert bad(summary="<strong>ok</strong> <em>ok</em>") == []
    assert bad(summary='<a href="http://x">enlace</a>') != []
    assert bad(experience={"Acme": ["<script>alert(1)</script>"]}) != []
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_validator.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `validator.py`**

Una función privada por regla, todas con la firma `(cv, adjustments, target, cover_letter) -> list[str]`, y `validate` las concatena. Cada motivo nombra dónde ocurrió (`resumen`, `Acme viñeta 2`, `carta: opening`). La regla 2 exime el campo `date` de la carta. En la regla 1 la exención de la carta se aplica quitando del texto las cadenas `context.company` y `context.role` antes de buscar vacíos.

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_validator.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add validator.py tests/test_validator.py
git commit -m "agregar el validador determinista de ajustes"
```

### Task 9: Objetivo

**Files:**
- Create: `targets.py`, `tests/test_targets.py`

**Interfaces:**
- Consumes: `vocabulary.Vocabulary`, `report.skill_weight`, `report.build_report`.
- Produces:
  - `from_offer(offer: dict, cv: dict, vocab: Vocabulary, lang: str | None = None) -> dict`; lanza `TargetError` si la oferta no tiene extracción.
  - `from_report(report: dict, cv: dict, vocab: Vocabulary, lang: str = "es") -> dict`; lanza `TargetError` si `n_offers == 0`.
  - Forma del objetivo:

```python
{
  "kind": "offer" | "family", "id": str, "label": str, "lang": "es" | "en",
  "profile": str,                      # familia si es clave de cv["profiles"]; si no, "default"
  "emphasize": [str],                  # canónicos covered/mentioned, por skill_weight desc
  "general_terms": {str: [str]},       # solo los declarados que el objetivo pide
  "gaps": [{"canonical": str, "forms": [str]}],
  "responsibilities": [str],
  "context": {"company": str, "role": str} | {"family": str, "n_offers": int},
  "source_text": str | None,           # texto crudo; solo kind == "offer"
}
```

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
def test_offer_target_classifies_skills(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"SnowSQL": "Snowflake"}, general_terms={"Lakehouse": ["Delta Lake"]})
    t = from_offer(mk("a", "data-engineer", ["Python", "Pandas", "Snowflake", "Lakehouse"], raw="TEXTO"), cv, v)
    assert t["kind"] == "offer" and t["profile"] == "data-engineer" and t["source_text"] == "TEXTO"
    assert set(t["emphasize"]) == {"Python", "Pandas"}
    assert t["general_terms"] == {"Lakehouse": ["Delta Lake"]}
    assert t["gaps"] == [{"canonical": "Snowflake", "forms": ["Snowflake", "SnowSQL"]}]

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
    assert t["kind"] == "family" and t["source_text"] is None and t["lang"] == "en"
    assert t["context"] == {"family": "data-engineer", "n_offers": 1}
    assert [g["canonical"] for g in t["gaps"]] == ["Snowflake"]

def test_empty_report_cannot_be_a_target(cv, tmp_path):
    v = vocab(cv, tmp_path)
    with pytest.raises(TargetError):
        from_report(build_report([], "data-engineer", v), cv, v)
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_targets.py -q`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `targets.py`**

`from_offer` construye internamente un informe de una sola oferta con `build_report` y delega en una función común, para que ambos tipos compartan el cálculo de `emphasize`, `general_terms` y `gaps`.

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_targets.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add targets.py tests/test_targets.py
git commit -m "agregar la construcción del objetivo desde una oferta o un informe"
```

### Task 10: Generador y `make apply OFFER=<id>`

**Files:**
- Rewrite: `tailor.py`
- Create: `tests/test_tailor.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes: `llm.complete_json`, `targets.from_offer`, `validator.validate`, `validator.entry_variants`, `build.apply_adjustments`, `build.{render_cv, render_cover_letter, copy_static_assets, add_pdf_metadata, generate_pdfs}`.
- Produces:
  - `material(cv: dict, lang: str) -> dict`: lo escrito a mano que recibe el modelo.
  - `generate(cv: dict, target: dict, complete=llm.complete_json) -> tuple[dict, dict | None]`: ajustes y carta; lanza `Rejected` (atributos `reasons` y `adjustments`).
  - `render(cv: dict, adjustments: dict, cover_letter: dict | None, out_dir: Path, *, label: str, html_only: bool = False) -> dict`: rutas generadas y `pages` (o `None` con `html_only`).
  - `run(target: dict, out_dir: Path, *, html_only=False, render_only=False, complete=llm.complete_json) -> dict`
  - `main(argv: list[str] | None = None) -> None`
  - `python tailor.py --offer ID [--lang es|en] [--html-only] [--render-only]`
  - Make: `apply OFFER= OFFER_LANG= HTML=1 RENDER=1`.
  - Archivos en `out_dir`: `adjustments.json`, `cover_letter.json`, `adjustments.rejected.json`.

- [ ] **Step 1: Escribir las pruebas que fallan**

`RESP` es una respuesta válida del modelo para el fixture `cv`, en la forma de listas que exige la API.

```python
def test_material_has_every_hand_written_variant(cv):
    m = material(cv, "es")
    acme = next(e for e in m["experience"] if e["company"] == "Acme")
    assert len(acme["variants"]) == 2
    assert set(m["titles"]) == {"AI Engineer | Machine Learning Engineer", "Data Engineer | Machine Learning Engineer"}
    assert {p["title"] for p in m["projects"]} == {"Agente A", "Sistema B"}     # incluye el oculto
    assert [e["company"] for e in material(cv, "en")["experience"]] == ["Acme"]

def test_generate_converts_lists_and_sets_profile_in_code(cv):
    adj, letter = generate(cv, TARGET, complete=fake(RESP))
    assert adj["experience"] == {"Acme": RESP["experience"][0]["bullets"]}
    assert adj["profile"] == TARGET["profile"] and adj["lang"] == "es"
    assert adj["target"] == {"kind": "offer", "id": TARGET["id"]}
    assert letter["opening"] == {"es": RESP["cover_letter"]["opening"]}

def test_family_target_gets_no_cover_letter(cv):
    assert generate(cv, {**TARGET, "kind": "family", "source_text": None}, complete=fake(RESP_NO_LETTER))[1] is None

def test_rejected_answer_is_retried_once_with_reasons(cv):
    complete = fake({**RESP, "summary": "Experto en Snowflake."}, RESP)
    generate(cv, TARGET, complete=complete)
    assert len(complete.prompts) == 2 and "Snowflake" in complete.prompts[1]

def test_two_rejections_raise_with_reasons(cv):
    bad = {**RESP, "summary": "Experto en Snowflake."}
    with pytest.raises(Rejected) as exc:
        generate(cv, TARGET, complete=fake(bad, bad))
    assert exc.value.reasons and exc.value.adjustments["summary"] == "Experto en Snowflake."

def test_run_writes_rejected_file_and_renders_nothing(cv, tmp_path, cv_file):
    bad = {**RESP, "summary": "Experto en Snowflake."}
    with pytest.raises(Rejected):
        run(TARGET, tmp_path, html_only=True, complete=fake(bad, bad))
    assert (tmp_path / "adjustments.rejected.json").exists()
    assert not list(tmp_path.glob("*.html"))

def test_run_html_only_writes_adjustments_and_html(cv, tmp_path, cv_file):
    out = run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    assert (tmp_path / "adjustments.json").exists() and out["pages"] is None
    assert list(tmp_path.glob("CV-*.html")) and list(tmp_path.glob("Carta-*.html"))

def test_render_only_revalidates_against_current_cv(cv, tmp_path, cv_file):
    run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    rename_company(cv_file, "Acme", "Acme Corp")         # cv.json cambió después
    with pytest.raises(Rejected) as exc:
        run(TARGET, tmp_path, html_only=True, render_only=True, complete=fake())
    assert any("Acme" in r for r in exc.value.reasons)

def test_generated_html_has_no_api_key(cv, tmp_path, cv_file, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSECRETO")
    run(TARGET, tmp_path, html_only=True, complete=fake(RESP))
    assert "AIzaSECRETO" not in next(tmp_path.glob("CV-*.html")).read_text()
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_tailor.py -q`
Expected: FAIL (el `tailor.py` actual no define `material`)

- [ ] **Step 3: Reescribir `tailor.py`**

Respuesta que se pide al modelo: `title` (cadena o `null`), `summary`, `experience_order` (lista), `experience` (lista de `{company, bullets}`), `tech_stack_order` (lista de `{category, first}`), `projects_shown`, `academic_shown` y, solo con `kind == "offer"`, `cover_letter` con los campos de `data/cover_letter.json` como cadenas y `why_me` como lista. El esquema se construye según `kind`.

El prompt conserva las reglas de `tailor.py:72-77` y agrega, con el contenido del objetivo: destacar `emphasize` en ese orden; no mencionar ningún término de `gaps`; un término de `general_terms` solo junto a una de sus habilidades; elegir y combinar entre `variants` sin superar el número de viñetas de la variante más larga; cada entrada cuenta una sola historia; solo `<strong>` y `<em>`; `title` debe salir de `titles`; el CV diseñado tiene un límite de 4 páginas.

`render` pasa `api_key=""` a `render_cv`: un CV que se va a enviar no lleva la clave de Gemini. Con PDF, cuenta páginas con `pypdf` después de `add_pdf_metadata` e imprime un aviso si son más de 4, indicando que se corrige quitando un proyecto de `projects_shown` o `academic_shown` y usando `RENDER=1`.

`run` con `render_only=True` lee `adjustments.json` y `cover_letter.json` de `out_dir`, valida y renderiza sin llamar al modelo. Sin `--offer` ni `--family`, `main` termina con código 1 y este mensaje: `Indica una oferta: make apply OFFER=<id>. Lista las disponibles con make offers-list; registra una nueva con make offer-add FILE=<archivo>.`

Los nombres de salida siguen el patrón actual (`tailor.py:260-267`), con `company_label` para una oferta.

- [ ] **Step 4: Actualizar el objetivo `apply` de `Makefile`**

```make
apply:
	uv run python tailor.py $(if $(OFFER),--offer $(OFFER),) $(if $(OFFER_LANG),--lang $(OFFER_LANG),) $(if $(HTML),--html-only,) $(if $(RENDER),--render-only,)
```

- [ ] **Step 5: Verificar que pasan**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tailor.py tests/test_tailor.py Makefile
git commit -m "unificar el generador de CV derivados con ajustes validados"
```

---

## Entrega 4: CV por familia

### Task 11: `make cv-market FAMILY=<familia>`

**Files:**
- Modify: `tailor.py`, `Makefile`, `tests/test_tailor.py`

**Interfaces:**
- Consumes: `offers.list_offers`, `report.{build_report, write_report}`, `targets.from_report`, `tailor.run`.
- Produces: `python tailor.py --family F [--lang es|en] [--since AAAA-MM-DD] [--html-only] [--render-only]`; Make `cv-market FAMILY= OFFER_LANG= SINCE= HTML=1 RENDER=1`. Salida en `applications/_market/<familia>/`.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
def test_family_run_writes_report_and_cv_without_letter(cv, tmp_path, cv_file, offers_dir):
    seed_offer("data-engineer", ["Python", "Snowflake"])
    out = tailor.main_family("data-engineer", tmp_path, lang="es", html_only=True, complete=fake(RESP_NO_LETTER))
    assert (tmp_path / "report.json").exists() and (tmp_path / "report.md").exists()
    assert (tmp_path / "adjustments.json").exists() and not list(tmp_path.glob("Carta-*"))
    assert out["weak_signal"] is True

def test_family_without_offers_fails_with_a_clear_message(cv, tmp_path, cv_file, offers_dir):
    with pytest.raises(targets.TargetError, match="data-engineer"):
        tailor.main_family("data-engineer", tmp_path, lang="es", html_only=True, complete=fake())

def test_unknown_family_is_rejected(cv, tmp_path, cv_file, offers_dir):
    with pytest.raises(SystemExit):
        tailor.main(["--family", "astronauta"])
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_tailor.py -q`
Expected: FAIL con `AttributeError: module 'tailor' has no attribute 'main_family'`

- [ ] **Step 3: Implementar `main_family` y el argumento `--family`**

`main_family(family, out_dir, *, lang, since=None, html_only=False, render_only=False, complete=llm.complete_json) -> dict`. Regenera el informe antes de construir el objetivo. `--offer` y `--family` son excluyentes. Con señal débil imprime el aviso y continúa. La etiqueta del nombre de archivo es la de `get_ats_outputs` en `build.py:279` para esa familia.

- [ ] **Step 4: Agregar el objetivo `cv-market` y verificar**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tailor.py tests/test_tailor.py Makefile
git commit -m "agregar el CV derivado por familia de cargo"
```

### Task 12: Documentación y comprobación con la oferta real

**Files:**
- Modify: `CLAUDE.md`, `README.md`, `Makefile` (`help`)

- [ ] **Step 1: Actualizar `CLAUDE.md`**

Reemplazar las entradas de `data/job_offer.json` y `data/job_offer_template.json` (líneas 14-15), la línea de `make apply` (56), el flujo "Tailored applications" (85) y las secciones "job_offer.json structure" (105-107) y "tailor.py internals" por el flujo nuevo: módulos y su responsabilidad, comandos, forma del archivo de oferta y del archivo de ajustes, las seis reglas del validador, y la regla de que solo `llm.py` importa `anthropic` y solo `offers.py` toca el historial. Enlazar los dos ADR y `GLOSSARY.md`.

- [ ] **Step 2: Actualizar `README.md` y `make help`**

Los comandos nuevos (`offer-add`, `offers-extract`, `offers-list`, `offers-report`, `apply OFFER=`, `cv-market`, `test`) con una línea cada uno.

- [ ] **Step 3: Comprobar con la oferta del 2026-11-19**

Gasta saldo (dos llamadas); requiere el visto bueno de Alejandro.

```bash
make offer-add FILE=applications/2026-11-19-reclutadora-ingenieria-datos-ia/offer.txt COMPANY="Reclutadora" ROLE="Ingeniería de Datos e IA"
make offers-report
make apply OFFER=<identificador que imprimió offer-add>
```

Expected:
- `offers-report` clasifica la oferta en una familia y lista como vacíos `Microsoft Fabric`, `ADK`, `LlamaIndex`, `MongoDB` y `BigQuery`; `NumPy` y `Azure Data Factory` aparecen como cubiertas.
- `make apply` termina sin rechazo del validador y con un PDF de 4 páginas o menos.
- `git status --short` no muestra `data/cv.json` modificado por estos comandos ni ningún archivo bajo `data/offers/` o `applications/`.

Comparar el resultado con el CV hecho a mano ese día (misma carpeta, `adjustments.json`) y anotar las diferencias para Alejandro.

- [ ] **Step 4: Verificar la suite y el build existente**

Run: `uv run pytest -q && make html`
Expected: PASS, y `make html` genera los 10 CV sin errores.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md README.md Makefile
git commit -m "documentar el historial de ofertas y los comandos nuevos"
```
