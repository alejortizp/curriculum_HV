# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bilingual (Spanish/English) professional CV for Alejandro Ortiz Perdomo (AI Engineer & Machine Learning Engineer). Both CVs are generated from a single data source (`data/cv.json`) using a Jinja2 template, then converted to PDF with Playwright.

## Key Files

- `data/cv.json` — **Single source of truth** for all CV content (edit this to update the CV)
- `templates/cv.html` — Jinja2 template (HTML structure + modal markup)
- `static/styles.css` — Shared CSS (page layout, print styles, markdown prose)
- `static/ai-suite.js` — Shared JS (PDF download, AI modal logic, Gemini API calls)
- `build.py` — Build script that generates HTMLs + PDFs
- `CV_español.html` / `CV_english.html` — Generated HTML files (do not edit directly)
- `CV_español.pdf` / `CV_english.pdf` — Generated PDF files (do not edit directly)

## Commands

### Build everything (HTML + PDF)

```bash
uv run python build.py
```

### Build HTML only (skip PDF generation)

```bash
uv run python build.py --html-only
```

### Build a single language

```bash
uv run python build.py es
uv run python build.py en
```

### Setup (first time only)

```bash
uv sync
uv run playwright install chromium
```

## Architecture

### Data flow

`data/cv.json` + `templates/cv.html` → `build.py` → HTML files → Playwright → PDF files

### cv.json structure

All translatable fields use `{"es": "...", "en": "..."}` objects. Fields with identical text in both languages use plain strings. Key sections:

- `personal` — Name, contact info, links (location is i18n)
- `profile` — Professional summary (i18n)
- `experience` — Work history. Each entry has a `langs` array (`["es", "en"]` or `["es"]`) to control which CV versions include it
- `projects` — Open source projects (i18n for title/description)
- `education` — Degrees and diplomas
- `tech_stack` — Skills grouped by category with star ratings (shared between languages)
- `power_skills`, `languages`, `certifications` — All i18n

### Template conventions

- The `t()` macro resolves i18n fields: `{{ t(entry.title) }}` returns the value for the current language
- The `stars()` macro generates star emojis from a number
- Use `cat['items']` (not `cat.items`) for tech_stack items to avoid conflict with Python dict `.items()` method
- UI strings (section titles, modal labels) are handled with `{% if lang == 'es' %}...{% else %}...{% endif %}` in the template
- The template renders a small inline `CV_CONFIG` object with language-specific strings and prompt functions, then loads `static/ai-suite.js` which reads from it

### Static files

- **`static/styles.css`** — All CSS: page layout (A4), `.item-no-break`, `.prose`, `@media print`. Edit here for styling changes.
- **`static/ai-suite.js`** — All JS logic: `downloadPDF()`, modal helpers, Gemini API calls, AI features. Reads config from the global `CV_CONFIG` object. Edit here for behavior changes.
- The `.page` class defines A4-sized pages (`21cm` wide, `29.7cm` min-height, `2.5cm`/`2cm` padding)
- Use `.item-no-break` only on small sidebar elements to prevent splitting across pages
- Use `.no-print` on UI elements that should not appear in PDFs (buttons, modals)
- The current/highlighted job entry uses `border-l-2 border-blue-600` and a blue badge for the date

### Gemini API key

Resolution order (first non-empty wins):
1. **Build-time** — `GEMINI_API_KEY` env var or `.env` file → injected into HTML by `build.py`
2. **Browser localStorage** — user-provided key saved as `gemini_api_key`
3. **Prompt** — when the user opens the AI modal without a key, they are prompted to enter one

The `.env` file is in `.gitignore`. See `.env.example` for the expected format.
