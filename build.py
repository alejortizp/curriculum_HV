#!/usr/bin/env python3
"""Build script: generates CV, cover letter, and portfolio HTML files from templates + data."""

import json
import os
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "cv.json"
COVER_LETTER_FILE = ROOT / "data" / "cover_letter.json"
TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_FILE = "cv.html"
COVER_LETTER_TEMPLATE = "cover_letter.html"

OUTPUTS = {
    "es": {"html": "CV_español.html", "pdf": "CV_español.pdf"},
    "en": {"html": "CV_english.html", "pdf": "CV_english.pdf"},
}

COVER_LETTER_OUTPUT = {
    "html": "Carta_Presentacion.html",
    "pdf": "Carta_Presentacion.pdf",
}

DOCS_DIR = ROOT / "docs"
PORTFOLIO_TEMPLATES = {
    "index": {"template": "portfolio_index.html", "output": "index.html"},
    "projects": {"template": "portfolio_projects.html", "output": "projects.html"},
    "contact": {"template": "portfolio_contact.html", "output": "contact.html"},
}


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_jinja_env() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)


def render_cv(cv_data: dict, lang: str, api_key: str) -> str:
    env = get_jinja_env()
    template = env.get_template(TEMPLATE_FILE)
    return template.render(cv=cv_data, lang=lang, api_key=api_key)


def render_cover_letter(cv_data: dict, letter_data: dict) -> str:
    env = get_jinja_env()
    template = env.get_template(COVER_LETTER_TEMPLATE)
    return template.render(cv=cv_data, letter=letter_data)


def generate_pdf(html_path: Path, pdf_path: Path, margin: dict):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin=margin,
        )
        page.close()
        browser.close()


def generate_cv_pdfs():
    from playwright.sync_api import sync_playwright

    margin = {"top": "1.5cm", "bottom": "1cm", "left": "0", "right": "0"}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang, files in OUTPUTS.items():
            html_path = (ROOT / files["html"]).resolve()
            pdf_path = ROOT / files["pdf"]
            page = browser.new_page()
            page.goto(f"file://{html_path}", wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin=margin,
            )
            page.close()
            print(f"  PDF: {pdf_path.name}")
        browser.close()


def build_cv(cv_data: dict, api_key: str, langs: list, html_only: bool):
    print("Generating CV HTML files...")
    for lang in langs:
        html = render_cv(cv_data, lang, api_key)
        output_path = ROOT / OUTPUTS[lang]["html"]
        output_path.write_text(html, encoding="utf-8")
        print(f"  HTML: {output_path.name}")

    if not html_only:
        print("Generating CV PDF files...")
        try:
            generate_cv_pdfs()
        except Exception as e:
            print(f"\n  Error generating PDFs: {e}")
            print("  Make sure Playwright is installed:")
            print("    uv run playwright install chromium")
            sys.exit(1)


def build_cover_letter(cv_data: dict, html_only: bool):
    if not COVER_LETTER_FILE.exists():
        print(f"  Cover letter data not found: {COVER_LETTER_FILE}")
        sys.exit(1)

    letter_data = load_json(COVER_LETTER_FILE)

    print("Generating cover letter...")
    html = render_cover_letter(cv_data, letter_data)
    html_path = ROOT / COVER_LETTER_OUTPUT["html"]
    html_path.write_text(html, encoding="utf-8")
    print(f"  HTML: {html_path.name}")

    if not html_only:
        pdf_path = ROOT / COVER_LETTER_OUTPUT["pdf"]
        try:
            margin = {"top": "0", "bottom": "0", "left": "0", "right": "0"}
            generate_pdf(html_path, pdf_path, margin)
            print(f"  PDF: {pdf_path.name}")
        except Exception as e:
            print(f"\n  Error generating PDF: {e}")
            print("  Make sure Playwright is installed:")
            print("    uv run playwright install chromium")
            sys.exit(1)


def build_portfolio(cv_data: dict):
    DOCS_DIR.mkdir(exist_ok=True)
    env = get_jinja_env()
    print("Generating portfolio pages...")
    for page_name, config in PORTFOLIO_TEMPLATES.items():
        template = env.get_template(config["template"])
        html = template.render(cv=cv_data, active_page=page_name)
        output_path = DOCS_DIR / config["output"]
        output_path.write_text(html, encoding="utf-8")
        print(f"  HTML: docs/{config['output']}")
    # Copy CV HTMLs to docs/ so "Descargar CV" links work on GitHub Pages
    for lang, files in OUTPUTS.items():
        src = ROOT / files["html"]
        if src.exists():
            shutil.copy2(src, DOCS_DIR / files["html"])
            print(f"  Copy: docs/{files['html']}")
        else:
            print(f"  Note: {files['html']} not found — run 'make html' first")
    # Copy profile photo to docs/ if source exists
    photo_src = ROOT / "static" / "profile.jpg"
    photo_dst = DOCS_DIR / "profile.jpg"
    if photo_src.exists():
        shutil.copy2(photo_src, photo_dst)
        print("  Copy: docs/profile.jpg")
    elif not photo_dst.exists():
        print("  Note: profile.jpg not found in static/ or docs/")
    # Create .nojekyll to prevent GitHub Pages Jekyll processing
    (DOCS_DIR / ".nojekyll").touch()
    print("Portfolio generated in docs/")


def get_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return api_key


def main():
    api_key = get_api_key()
    cv_data = load_json(DATA_FILE)
    html_only = "--html-only" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # uv run python build.py carta
    if "carta" in args:
        build_cover_letter(cv_data, html_only)
        print("\nDone!")
        return

    # uv run python build.py portfolio
    if "portfolio" in args:
        build_portfolio(cv_data)
        print("\nDone!")
        return

    # uv run python build.py [es|en] [--html-only]
    langs = list(OUTPUTS.keys())
    if args and args[0] in OUTPUTS:
        langs = [args[0]]

    build_cv(cv_data, api_key, langs, html_only)
    print("\nDone!")


if __name__ == "__main__":
    main()
