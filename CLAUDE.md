# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bilingual (Spanish/English) professional CV for Alejandro Ortiz Perdomo (AI Engineer & Machine Learning Engineer). The CVs are standalone HTML files styled with Tailwind CSS via CDN — there is no build step or bundler.

## Key Files

- `CV_español.html` — Spanish CV (self-contained HTML)
- `CV_english.html` — English CV (self-contained HTML)
- `CV_español.pdf` / `CV_english.pdf` — Generated PDFs (do not edit directly)

## Commands

### Generate PDFs from HTML (requires Playwright installed globally)

```bash
npx playwright pdf CV_español.html CV_español.pdf
npx playwright pdf CV_english.html CV_english.pdf
```

If CDN resources fail to load, use the full file path:

```bash
npx playwright pdf file://$(pwd)/CV_español.html CV_español.pdf
npx playwright pdf file://$(pwd)/CV_english.html CV_english.pdf
```

### Python environment (uv, Python 3.13)

```bash
uv run main.py
```

## Architecture

Each HTML file is a **fully self-contained** single-page application with no shared code between them. Changes to one must be manually mirrored to the other if they should stay in sync.

### Structure within each HTML file

1. **CDN dependencies** (in `<head>`): Tailwind CSS, Font Awesome 6, Lucide icons, marked.js (Markdown rendering), html2pdf.js
2. **Print styles** (`@media print`): A4 layout, `page-break-inside: avoid` via `.item-no-break` class, color preservation with `print-color-adjust: exact`
3. **CV content** (in `<body>`): Two-column layout — left sidebar (contact info, skills, certifications, languages) and main content (experience, education, projects)
4. **Floating PDF button** (class `no-print`): Uses html2pdf.js for in-browser PDF download
5. **AI Career Suite modal** (class `no-print`): Interactive tools powered by Gemini API — Elevator Pitch, Technical Interview, Cover Letter, Gap Analysis

### Important conventions

- The `.page` class defines A4-sized pages (`21cm` wide, `29.7cm` min-height, `2.5cm`/`2cm` padding)
- Use `.item-no-break` only on small sidebar elements to prevent splitting across pages — do NOT apply it to large main-column content blocks
- Use `.no-print` on UI elements that should not appear in PDFs (buttons, modals)
- The Gemini API key is stored inline in a `<script>` tag (variable `apiKey`). It is currently empty and must be set by the user
- Both files use the same visual design and CSS but are independent — keep styling synchronized manually
