#!/usr/bin/env python3
"""Build script: generates CV HTML files from template + data, then PDFs with Playwright."""

import json
import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "cv.json"
TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_FILE = "cv.html"

OUTPUTS = {
    "es": {"html": "CV_español.html", "pdf": "CV_español.pdf"},
    "en": {"html": "CV_english.html", "pdf": "CV_english.pdf"},
}


def load_data() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def render_html(cv_data: dict, lang: str, api_key: str) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template(TEMPLATE_FILE)
    return template.render(cv=cv_data, lang=lang, api_key=api_key)


def generate_pdfs():
    from playwright.sync_api import sync_playwright

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
                margin={"top": "1.5cm", "bottom": "1cm", "left": "0", "right": "0"},
            )
            page.close()
            print(f"  PDF: {pdf_path.name}")
        browser.close()


def main():
    # Gemini API key: read from env or .env file, default empty
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    cv_data = load_data()

    # Determine which languages to build
    langs = list(OUTPUTS.keys())
    if len(sys.argv) > 1 and sys.argv[1] in OUTPUTS:
        langs = [sys.argv[1]]

    # Check for --html-only flag
    html_only = "--html-only" in sys.argv

    print("Generating HTML files...")
    for lang in langs:
        html = render_html(cv_data, lang, api_key)
        output_path = ROOT / OUTPUTS[lang]["html"]
        output_path.write_text(html, encoding="utf-8")
        print(f"  HTML: {output_path.name}")

    if not html_only:
        print("Generating PDF files...")
        try:
            generate_pdfs()
        except Exception as e:
            print(f"\n  Error generating PDFs: {e}")
            print("  Make sure Playwright is installed:")
            print("    uv run playwright install chromium")
            sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
