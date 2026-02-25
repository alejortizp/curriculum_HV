# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bilingual (Spanish/English) professional CV for Alejandro Ortiz Perdomo (AI Engineer & Machine Learning Engineer). Both CVs are generated from a single data source (`data/cv.json`) using a Jinja2 template, then converted to PDF with Playwright. Also includes a reusable cover letter system and a bilingual portfolio website deployed to GitHub Pages.

## Key Files

- `data/cv.json` — **Single source of truth** for all CV content (edit this to update the CV)
- `data/cover_letter.json` — Cover letter content, bilingual (edit per company)
- `data/cover_letter_template.json` — Blank cover letter template (copy to create new letters)
- `templates/cv.html` — Jinja2 template for CVs (HTML structure, JSON-LD, modal after article)
- `templates/cover_letter.html` — Jinja2 template for cover letter (bilingual, reuses CV header)
- `templates/portfolio_base.html` — Portfolio base template (nav, footer, SEO, language switcher, i18n macros)
- `templates/portfolio_index.html` — Portfolio home page (hero, about, skills)
- `templates/portfolio_projects.html` — Portfolio projects page (iterated from cv.json)
- `templates/portfolio_contact.html` — Portfolio contact page (Formspree form)
- `static/styles.css` — Shared CSS (page layout, print styles, markdown prose, responsive, a11y)
- `static/ai-suite.js` — Shared JS (PDF download via pre-generated file, AI modal logic, Gemini API calls)
- `static/profile.jpg` — Profile photo (canonical source, copied to docs/ during build)
- `build.py` — Build script (argparse CLI) that generates HTMLs + PDFs (CVs, cover letter, bilingual portfolio)
- `docs/` — Generated portfolio + CVs + PDFs for GitHub Pages (do not edit directly)
- `docs/index.html` / `docs/index_en.html` — Portfolio home (ES/EN)
- `docs/projects.html` / `docs/projects_en.html` — Portfolio projects (ES/EN)
- `docs/contact.html` / `docs/contact_en.html` — Portfolio contact (ES/EN)
- `docs/CV_español.html` / `docs/CV_english.html` — Generated CV files, default profile
- `docs/CV_español_<profile>.html` / `docs/CV_english_<profile>.html` — Profile variant CVs (ai-engineer, ml-engineer, mlops)
- `docs/CV-Alejandro-Ortiz-Perdomo-*.pdf` — ASCII-safe PDF copies for GitHub Pages download button
- `docs/sitemap.xml` / `docs/robots.txt` — Auto-generated SEO files
- `docs/static/` — Copy of styles.css + ai-suite.js (needed by CVs in docs/)
- `Carta_Presentacion.html` / `Cover_Letter.html` — Generated cover letters ES/EN (do not edit)

## Commands

```bash
make              # Build everything: all CV profiles (HTML + PDF) + bilingual portfolio
make build        # Build all profiles × both languages (8 CVs: 4 profiles × 2 langs)
make html         # Build HTML only (skip PDF), all profiles
make es           # Build Spanish CVs only (all profiles)
make en           # Build English CVs only (all profiles)
make carta        # Build cover letter (HTML + PDF, both languages)
make carta-es     # Build cover letter - Spanish only
make carta-en     # Build cover letter - English only
make portfolio    # Build bilingual portfolio in docs/ (6 pages: 3 ES + 3 EN)
make setup        # First-time setup (uv sync + playwright)
make clean        # Remove all generated files (all profiles + portfolio)
make open-es      # Build HTML and open Spanish CV in browser
make open-en      # Build HTML and open English CV in browser
make open-carta   # Build and open cover letter (ES) in browser
make open-carta-en # Build and open cover letter (EN) in browser
make open-portfolio # Build and open portfolio in browser
make help         # Show all targets
```

CV targets accept a `PROFILE` variable to build a single profile: `make es PROFILE=ai-engineer`. Without `PROFILE`, **all profiles are built** (default, ai-engineer, ml-engineer, mlops). Available profiles are defined in `cv.json` → `profiles`.

Output naming: default profile uses `CV_español.html` / `CV_english.html`. Profile variants use `CV_español_<profile>.html` / `CV_english_<profile>.html` (e.g., `CV_español_ai-engineer.html`). PDFs use ASCII-safe names: `CV-Alejandro-Ortiz-Perdomo-ES.pdf`, `CV-Alejandro-Ortiz-Perdomo-AI-Engineer-EN.pdf`, etc.

`make` (default) runs `build` + `portfolio`, so updating `cv.json` and running `make` regenerates all 8 CVs, PDFs, and the bilingual portfolio in one step.

The Makefile wraps `uv run python build.py` with various flags. `build.py` uses **argparse** — run `uv run python build.py --help` for usage. Example: `uv run python build.py es --html-only --profile ai-engineer`.

## Architecture

### Data flow

- **CVs:** `data/cv.json` + `templates/cv.html` → `build.py` → `docs/CV_*.html` (all profiles) + copies `static/` to `docs/static/` → Playwright → PDF files in root (with pypdf metadata injection) + copies to `docs/`
- **Cover letter:** `data/cover_letter.json` + `data/cv.json` (personal info) + `templates/cover_letter.html` → `build.py carta` → `Carta_Presentacion.html` + `Cover_Letter.html` → Playwright → PDFs (with pypdf metadata)
- **Portfolio:** `data/cv.json` + `templates/portfolio_*.html` → `build.py portfolio` → `docs/` (6 pages: index, projects, contact × ES/EN) + `sitemap.xml` + `robots.txt`. CVs are already in docs/ from the build step

### cv.json structure

All translatable fields use `{"es": "...", "en": "..."}` objects. Fields with identical text in both languages use plain strings. Key sections:

- `personal` — Name, contact info, links (with `display_url` for ATS-visible URLs), portfolio URL, formspree_id, google_analytics_id (location is i18n)
- `profiles` — Professional summary variants keyed by role name (default, ai-engineer, ml-engineer, mlops). Each variant has `{"es": "...", "en": "..."}`. Without `--profile`, all profiles are built. `build.py --profile <name>` filters to one; resolved to `cv.profile` before rendering so the template just reads `cv.profile[lang]`
- `experience` — Work history. Each entry has a `langs` array (`["es", "en"]` or `["es"]`) to control which CV versions include it
- `projects` — Open source projects (i18n for title/description)
- `education` — Degrees and diplomas
- `tech_stack` — Skills grouped by category with `years` field (years of experience, displayed as "N+" in the CV). Each skill is an individual item (no compound "A/B" entries). Shared between languages
- `power_skills`, `languages`, `certifications` — All i18n

### cover_letter.json structure

Bilingual cover letter data. All text fields use i18n `{"es": "...", "en": "..."}` objects. `why_me` uses `{"es": [...], "en": [...]}` for the bullet point arrays. Fields: `company`, `recipient`, `role`, `date`, `subject`, `greeting`, `opening`, `why_me_title` + `why_me`, `differentiator_title` + `differentiator`, `closing`, `farewell`, `sign_off`. Personal info (name, contact, title, portfolio link) is pulled from `cv.json`. Use `data/cover_letter_template.json` as a starting point for new letters.

### Template conventions

- The `t()` macro resolves i18n fields: `{{ t(entry.title) }}` returns the value for the current language. Defined in both `cv.html` and `portfolio_base.html`
- Tech stack skills use `years` field displayed as `N+` in blue. The section header includes "(años exp.)" / "(years exp.)" as context
- Use `cat['items']` (not `cat.items`) for tech_stack items to avoid conflict with Python dict `.items()` method
- UI strings (section titles, modal labels) are handled with `{% if lang == 'es' %}...{% else %}...{% endif %}` in the template
- The CV template renders a small inline `CV_CONFIG` object with language-specific strings and prompt functions, then loads `static/ai-suite.js` which reads from it
- `build.py` passes `pdf_filename` and `profile_name` to CV templates; `lang`, `page_suffix`, and `other_page_suffix` to portfolio templates
- Portfolio nav links use `href="index{{ page_suffix }}.html"` for same-language navigation
- Language switcher uses `href="{{ active_page }}{{ other_page_suffix }}.html"` to link to the other language

### ATS / OCR optimization

The CV template is optimized for Applicant Tracking Systems and OCR extraction:

- **JSON-LD** enriched structured data (schema.org `Person`) with `worksFor`, `alumniOf`, `knowsAbout`, `description`, `image`
- **Visible URLs** in header: `display_url` fields in cv.json shown as link text (e.g., `linkedin.com/in/...`) so PDF extractors capture the URLs
- **Modal after article**: floating buttons and AI modal are placed after `</article>` so ATS parsers read CV content first
- **Tagged PDFs**: Playwright generates tagged (`tagged=True`) and outlined (`outline=True`) PDFs for accessibility and ATS parsing
- **PDF metadata**: pypdf injects author, title, and subject metadata into generated PDFs
- **ASCII-safe PDF filenames**: `CV-Alejandro-Ortiz-Perdomo-ES.pdf` (no accented characters; ATS-friendly)
- **Searchable PDFs**: the "Save PDF" button downloads the Playwright-generated PDF (searchable text), not an html2pdf.js image-based PDF
- **ATS section headers**: standard titles (Professional Summary, Technical Skills, Key Skills) instead of creative names
- **Individual skills**: each skill is a separate item (no compound "A/B" entries) for better ATS keyword matching
- **Project title/URL separator**: `—` between project name and URL prevents text concatenation in PDF extraction
- **Font fallback chain**: `Inter` → system fonts (`-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, ...`) for reliable rendering
- **Consistent dates**: all date ranges use en-dash `–` (not hyphen `-`)
- **Meta keywords**: relevant terms for search engine indexing
- Font Awesome icons and emojis have `aria-hidden="true"` for accessibility
- **Page margins**: CSS is the single source of truth — `.page` print styles handle all padding, Playwright margins are zero

### Static files

- **`static/styles.css`** — All CSS: page layout (A4), `.item-no-break`, `.prose`, `@page` rule (zero margins), `@media print` (section break control, orphans/widows, section heading orphan prevention), mobile responsive (`max-width: 850px`), `prefers-reduced-motion`, `focus-visible` styles, system font fallback chain. Edit here for styling changes.
- **`static/ai-suite.js`** — All JS logic: `downloadPDF()` (serves pre-generated Playwright PDF), modal helpers (focus trap, Escape key, `aria-live` on results), Gemini API calls, AI features. Reads config from the global `CV_CONFIG` object (includes `pdfUrl` and `pdfFilename`). Edit here for behavior changes.
- The `.page` class defines A4-sized pages (`21cm` wide, `29.7cm` min-height, `2.5cm`/`2cm` padding)
- Use `.item-no-break` on any element that should not split across pages (experience entries, projects, sidebar items)
- Use `.no-print` on UI elements that should not appear in PDFs (buttons, modals)
- The current/highlighted job entry uses `border-l-2 border-blue-600` and a blue badge for the date

### SEO

- **Preconnect hints** for CDNs (`cdnjs.cloudflare.com`, `cdn.tailwindcss.com`, `cdn.jsdelivr.net`, `unpkg.com`)
- **og:image** with `width`, `height`, and `alt` attributes
- **profile OG tags**: `profile:first_name`, `profile:last_name`
- **hreflang** tags on all pages (CV and portfolio) linking ES/EN variants
- **Canonical URLs** on all pages
- **sitemap.xml** and **robots.txt** auto-generated during portfolio build
- **BreadcrumbList JSON-LD** on portfolio projects and contact pages
- **WebSite + Person JSON-LD** `@graph` in portfolio base template

### Accessibility (WCAG)

- **Skip navigation** link on all pages
- **aria-live** regions on AI modal loading/result areas
- **Focus management**: result area focused after AI response, modal focus trap with Escape to close
- **aria-expanded** on dropdown and mobile menu buttons (dynamically toggled via JS)
- **aria-pressed** on filter buttons, **aria-haspopup="menu"** and **role="menu"/"menuitem"** on CV dropdown
- **aria-labelledby** on major portfolio sections
- **aria-required** and **autocomplete** attributes on form inputs
- **aria-busy** on contact form submit button during loading
- **aria-label** on social icon links
- **prefers-reduced-motion** media query disables animations
- **focus-visible** styles on modal and floating buttons
- `rel="noopener noreferrer"` on all `target="_blank"` links

### Portfolio (GitHub Pages)

- **Bilingual**: all pages generated in ES (default, no suffix) and EN (`_en` suffix). Language switcher in nav
- Portfolio templates extend `portfolio_base.html` (shared nav, footer, SEO meta tags, `t()` macro, language switcher)
- Data comes from `cv.json` — portfolio stays in sync with the CV automatically. Projects, skills, contact info, and links are all dynamic
- CV HTMLs are generated directly in `docs/` by `build.py` (not copied). `static/styles.css` and `static/ai-suite.js` are copied to `docs/static/` during CV build
- `build.py portfolio` generates 6 portfolio pages in `docs/`, copies `static/profile.jpg`, generates `sitemap.xml` + `robots.txt`
- `.nojekyll` file is created to prevent GitHub Pages Jekyll processing
- Contact form uses Formspree (AJAX submit, no redirect). The Formspree ID is in `cv.json` → `personal.formspree_id`
- Google Analytics is optional — set `personal.google_analytics_id` in `cv.json` (gtag.js script is conditionally injected only when the ID has a value)
- Mobile menu: hamburger button toggles a slide-in panel with overlay (JS in base template)
- "Descargar CV" / "Download CV" button on index page has a dropdown with both language options (ES/EN)
- `profile.jpg` canonical source is `static/profile.jpg` — build copies it to `docs/`
- Tailwind CSS custom color tokens: `primary`, `primary-hover`, `surface-secondary`, `surface-secondary-hover`, `border-dark`, `text-secondary`
- GitHub Pages serves from `docs/` folder on `main` branch
- URL: https://alejortizp.github.io/curriculum_HV/

### build.py internals

- Uses **argparse** for CLI parsing (same interface as before, but with `--help` support)
- **Jinja2 Environment** is cached (singleton) across all template renders
- **PDF metadata**: after Playwright PDF generation, `pypdf` injects `/Title`, `/Author`, `/Subject`, `/Creator` into each PDF
- **DRY error handling**: `_handle_pdf_error()` helper shared by CV and cover letter builds
- **Portfolio language loop**: iterates `PORTFOLIO_LANGS = {"es": "", "en": "_en"}`, passes `lang`, `page_suffix`, `other_page_suffix` to templates
- Font await fix: uses `async () => { await document.fonts.ready; }` (properly awaits the Promise)

### Gemini API key

Resolution order (first non-empty wins):
1. **Build-time** — `GEMINI_API_KEY` env var or `.env` file → injected into HTML by `build.py`
2. **Browser localStorage** — user-provided key saved as `gemini_api_key`
3. **Prompt** — when the user opens the AI modal without a key, they are prompted to enter one

The `.env` file is in `.gitignore`. See `.env.example` for the expected format.
