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
    "es": {"html": "docs/CV_español.html", "pdf": "CV_español.pdf"},
    "en": {"html": "docs/CV_english.html", "pdf": "CV_english.pdf"},
}

COVER_LETTER_OUTPUTS = {
    "es": {"html": "Carta_Presentacion.html", "pdf": "Carta_Presentacion.pdf"},
    "en": {"html": "Cover_Letter.html", "pdf": "Cover_Letter.pdf"},
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


def render_cover_letter(cv_data: dict, letter_data: dict, lang: str) -> str:
    env = get_jinja_env()
    template = env.get_template(COVER_LETTER_TEMPLATE)
    return template.render(cv=cv_data, letter=letter_data, lang=lang)


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
    # Ensure docs/ and docs/static/ exist for CV output
    DOCS_DIR.mkdir(exist_ok=True)
    docs_static = DOCS_DIR / "static"
    docs_static.mkdir(exist_ok=True)
    for fname in ("styles.css", "ai-suite.js"):
        src = ROOT / "static" / fname
        if src.exists():
            shutil.copy2(src, docs_static / fname)
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
            # Copy PDFs to docs/ for GitHub Pages download button
            for lang, files in OUTPUTS.items():
                pdf_src = ROOT / files["pdf"]
                pdf_dst = DOCS_DIR / files["pdf"]
                if pdf_src.exists():
                    shutil.copy2(pdf_src, pdf_dst)
                    print(f"  Copy: docs/{files['pdf']}")
        except Exception as e:
            print(f"\n  Error generating PDFs: {e}")
            print("  Make sure Playwright is installed:")
            print("    uv run playwright install chromium")
            sys.exit(1)


def build_cover_letter(cv_data: dict, html_only: bool, langs: list = None):
    if langs is None:
        langs = list(COVER_LETTER_OUTPUTS.keys())

    if not COVER_LETTER_FILE.exists():
        print(f"  Cover letter data not found: {COVER_LETTER_FILE}")
        sys.exit(1)

    letter_data = load_json(COVER_LETTER_FILE)

    print("Generating cover letter...")
    for lang in langs:
        html = render_cover_letter(cv_data, letter_data, lang)
        output = COVER_LETTER_OUTPUTS[lang]
        html_path = ROOT / output["html"]
        html_path.write_text(html, encoding="utf-8")
        print(f"  HTML: {html_path.name}")

        if not html_only:
            pdf_path = ROOT / output["pdf"]
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
    # Verify CV HTMLs exist in docs/ (generated by 'make build')
    for lang, files in OUTPUTS.items():
        cv_path = ROOT / files["html"]
        if not cv_path.exists():
            print(f"  Note: {files['html']} not found — run 'make build' first")
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

    # Extract --profile flag
    profile_name = "default"
    if "--profile" in sys.argv:
        idx = sys.argv.index("--profile")
        if idx + 1 < len(sys.argv):
            profile_name = sys.argv[idx + 1]

    # Resolve profile variant: profiles.{name} → profile (template reads cv.profile[lang])
    if "profiles" in cv_data:
        if profile_name in cv_data["profiles"]:
            cv_data["profile"] = cv_data["profiles"][profile_name]
            if profile_name != "default":
                print(f"Using profile: {profile_name}")
        else:
            available = ", ".join(cv_data["profiles"].keys())
            print(f"Warning: profile '{profile_name}' not found (available: {available})")
            print("Using default profile.")
            cv_data["profile"] = cv_data["profiles"]["default"]

    args = [a for a in sys.argv[1:] if not a.startswith("--") and a != profile_name]

    # uv run python build.py carta [carta-es|carta-en]
    if "carta" in args or "carta-es" in args or "carta-en" in args:
        carta_langs = list(COVER_LETTER_OUTPUTS.keys())
        if "carta-es" in args:
            carta_langs = ["es"]
        elif "carta-en" in args:
            carta_langs = ["en"]
        build_cover_letter(cv_data, html_only, carta_langs)
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
