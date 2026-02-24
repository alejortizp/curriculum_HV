# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bilingual (Spanish/English) professional CV for Alejandro Ortiz Perdomo (AI Engineer & Machine Learning Engineer). Both CVs are generated from a single data source (`data/cv.json`) using a Jinja2 template, then converted to PDF with Playwright. Also includes a reusable cover letter system and a portfolio website deployed to GitHub Pages.

## Key Files

- `data/cv.json` — **Single source of truth** for all CV content (edit this to update the CV)
- `data/cover_letter.json` — Cover letter content, bilingual (edit per company)
- `data/cover_letter_template.json` — Blank cover letter template (copy to create new letters)
- `templates/cv.html` — Jinja2 template for CVs (HTML structure + modal markup)
- `templates/cover_letter.html` — Jinja2 template for cover letter (bilingual, reuses CV header)
- `static/styles.css` — Shared CSS (page layout, print styles, markdown prose)
- `static/ai-suite.js` — Shared JS (PDF download, AI modal logic, Gemini API calls)
- `static/profile.jpg` — Profile photo (canonical source, copied to docs/ during build)
- `build.py` — Build script that generates HTMLs + PDFs (CVs, cover letter, portfolio)
- `docs/CV_español.html` / `docs/CV_english.html` — Generated CV files (in docs/, do not edit)
- `Carta_Presentacion.html` / `Cover_Letter.html` — Generated cover letters ES/EN (do not edit)
- `docs/` — Generated portfolio + CVs for GitHub Pages (do not edit directly)
- `docs/static/` — Copy of styles.css + ai-suite.js (needed by CVs in docs/)

## Commands

```bash
make              # Build everything: CVs (HTML + PDF) + portfolio in docs/
make build        # Build CVs only (HTML + PDF, both languages)
make html         # Build HTML only (skip PDF)
make es           # Build Spanish CV only
make en           # Build English CV only
make carta        # Build cover letter (HTML + PDF, both languages)
make carta-es     # Build cover letter - Spanish only
make carta-en     # Build cover letter - English only
make portfolio    # Build portfolio in docs/ (GitHub Pages)
make setup        # First-time setup (uv sync + playwright)
make clean        # Remove all generated files
make open-es      # Build HTML and open Spanish CV in browser
make open-en      # Build HTML and open English CV in browser
make open-carta   # Build and open cover letter (ES) in browser
make open-carta-en # Build and open cover letter (EN) in browser
make open-portfolio # Build and open portfolio in browser
make help         # Show all targets
```

CV targets accept a `PROFILE` variable: `make es PROFILE=ai-engineer`. Available profiles are defined in `cv.json` → `profiles` (default, ai-engineer, ml-engineer, mlops).

`make` (default) runs `build` + `portfolio`, so updating `cv.json` and running `make` regenerates CVs, PDFs, and the portfolio in one step.

The Makefile wraps `uv run python build.py` with various flags. You can also call build.py directly for combined flags (e.g., `uv run python build.py es --html-only --profile ai-engineer`).

## Architecture

### Data flow

- **CVs:** `data/cv.json` + `templates/cv.html` → `build.py` → `docs/CV_*.html` + copies `static/` to `docs/static/` → Playwright → PDF files in root
- **Cover letter:** `data/cover_letter.json` + `data/cv.json` (personal info) + `templates/cover_letter.html` → `build.py carta` → `Carta_Presentacion.html` + `Cover_Letter.html` → Playwright → PDFs
- **Portfolio:** `data/cv.json` + `templates/portfolio_*.html` → `build.py portfolio` → `docs/` (index.html, projects.html, contact.html). CVs are already in docs/ from the build step

### cv.json structure

All translatable fields use `{"es": "...", "en": "..."}` objects. Fields with identical text in both languages use plain strings. Key sections:

- `personal` — Name, contact info, links, portfolio URL, formspree_id, google_analytics_id (location is i18n)
- `profiles` — Professional summary variants keyed by role name (default, ai-engineer, ml-engineer, mlops). Each variant has `{"es": "...", "en": "..."}`. `build.py --profile <name>` selects which one to use; resolved to `cv.profile` before rendering so the template just reads `cv.profile[lang]`
- `experience` — Work history. Each entry has a `langs` array (`["es", "en"]` or `["es"]`) to control which CV versions include it
- `projects` — Open source projects (i18n for title/description)
- `education` — Degrees and diplomas
- `tech_stack` — Skills grouped by category with `years` field (years of experience, displayed as "N+" in the CV). Shared between languages
- `power_skills`, `languages`, `certifications` — All i18n

### cover_letter.json structure

Bilingual cover letter data. All text fields use i18n `{"es": "...", "en": "..."}` objects. `why_me` uses `{"es": [...], "en": [...]}` for the bullet point arrays. Fields: `company`, `recipient`, `role`, `date`, `subject`, `greeting`, `opening`, `why_me_title` + `why_me`, `differentiator_title` + `differentiator`, `closing`, `farewell`, `sign_off`. Personal info (name, contact, title, portfolio link) is pulled from `cv.json`. Use `data/cover_letter_template.json` as a starting point for new letters.

### Template conventions

- The `t()` macro resolves i18n fields: `{{ t(entry.title) }}` returns the value for the current language
- Tech stack skills use `years` field displayed as `N+` in blue (no more star emojis). The section header includes "(años exp.)" / "(years exp.)" as context
- Use `cat['items']` (not `cat.items`) for tech_stack items to avoid conflict with Python dict `.items()` method
- UI strings (section titles, modal labels) are handled with `{% if lang == 'es' %}...{% else %}...{% endif %}` in the template
- The template renders a small inline `CV_CONFIG` object with language-specific strings and prompt functions, then loads `static/ai-suite.js` which reads from it

### Static files

- **`static/styles.css`** — All CSS: page layout (A4), `.item-no-break`, `.prose`, `@page` rule (zero margins), `@media print` (section break control, orphans/widows). Edit here for styling changes.
- **`static/ai-suite.js`** — All JS logic: `downloadPDF()`, modal helpers, Gemini API calls, AI features. Reads config from the global `CV_CONFIG` object. Edit here for behavior changes.
- The `.page` class defines A4-sized pages (`21cm` wide, `29.7cm` min-height, `2.5cm`/`2cm` padding)
- Use `.item-no-break` on any element that should not split across pages (experience entries, projects, sidebar items)
- Use `.no-print` on UI elements that should not appear in PDFs (buttons, modals)
- The current/highlighted job entry uses `border-l-2 border-blue-600` and a blue badge for the date

### Portfolio (GitHub Pages)

- Portfolio templates extend `portfolio_base.html` (shared nav with active page highlight + footer + SEO meta tags)
- Data comes from `cv.json` — portfolio stays in sync with the CV automatically. Projects, skills, contact info, and links are all dynamic
- CV HTMLs are generated directly in `docs/` by `build.py` (not copied). `static/styles.css` and `static/ai-suite.js` are copied to `docs/static/` during CV build so relative paths work both locally and on GitHub Pages
- `build.py portfolio` generates portfolio HTML pages in `docs/`, copies `static/profile.jpg` there
- `.nojekyll` file is created to prevent GitHub Pages Jekyll processing
- Contact form uses Formspree (AJAX submit, no redirect). The Formspree ID is in `cv.json` → `personal.formspree_id`
- Google Analytics is optional — set `personal.google_analytics_id` in `cv.json` (gtag.js script is conditionally injected only when the ID has a value)
- Mobile menu: hamburger button toggles a slide-in panel with overlay (JS in base template)
- "Descargar CV" button on index page has a dropdown with both language options (ES/EN)
- `profile.jpg` canonical source is `static/profile.jpg` — build copies it to `docs/`
- GitHub Pages serves from `docs/` folder on `main` branch
- URL: https://alejortizp.github.io/curriculum_HV/

### Gemini API key

Resolution order (first non-empty wins):
1. **Build-time** — `GEMINI_API_KEY` env var or `.env` file → injected into HTML by `build.py`
2. **Browser localStorage** — user-provided key saved as `gemini_api_key`
3. **Prompt** — when the user opens the AI modal without a key, they are prompted to enter one

The `.env` file is in `.gitignore`. See `.env.example` for the expected format.
