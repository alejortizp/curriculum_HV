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

# Default output paths (also used by portfolio to verify CV files exist)
OUTPUTS = {
    "es": {"html": "docs/CV_español.html", "pdf": "CV-Alejandro-Ortiz-Perdomo-ES.pdf"},
    "en": {"html": "docs/CV_english.html", "pdf": "CV-Alejandro-Ortiz-Perdomo-EN.pdf"},
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


_jinja_env: Environment | None = None


def get_jinja_env() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    return _jinja_env


def get_outputs(profile_name: str) -> dict:
    """Return output paths for a given profile. Default profile has no suffix."""
    if profile_name == "default":
        return OUTPUTS
    suffix = f"_{profile_name}"
    # ASCII-safe PDF name: profile name with known acronyms uppercased
    _acronyms = {"ai", "ml", "mlops"}
    profile_label = "-".join(
        w.upper() if w.lower() in _acronyms else w.capitalize()
        for w in profile_name.split("-")
    )
    return {
        "es": {"html": f"docs/CV_español{suffix}.html", "pdf": f"CV-Alejandro-Ortiz-Perdomo-{profile_label}-ES.pdf"},
        "en": {"html": f"docs/CV_english{suffix}.html", "pdf": f"CV-Alejandro-Ortiz-Perdomo-{profile_label}-EN.pdf"},
    }


def render_cv(cv_data: dict, lang: str, api_key: str, pdf_filename: str = "",
              profile_name: str = "default") -> str:
    env = get_jinja_env()
    template = env.get_template(TEMPLATE_FILE)
    return template.render(cv=cv_data, lang=lang, api_key=api_key,
                           pdf_filename=pdf_filename, profile_name=profile_name)


def render_cover_letter(cv_data: dict, letter_data: dict, lang: str) -> str:
    env = get_jinja_env()
    template = env.get_template(COVER_LETTER_TEMPLATE)
    return template.render(cv=cv_data, letter=letter_data, lang=lang)


def _handle_pdf_error(e: Exception) -> None:
    """Print PDF generation error and exit."""
    print(f"\n  Error generating PDFs: {e}")
    print("  Make sure Playwright is installed:")
    print("    uv run playwright install chromium")
    sys.exit(1)


def generate_pdfs(jobs: list, margin: dict):
    """Generate PDFs in a single browser session.

    jobs: list of {"html": str, "pdf": str} dicts (paths relative to ROOT).
    margin: dict with top/bottom/left/right CSS values.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for files in jobs:
            html_path = (ROOT / files["html"]).resolve()
            pdf_path = ROOT / files["pdf"]
            page = browser.new_page()
            page.goto(f"file://{html_path}", wait_until="networkidle")
            page.evaluate("async () => { await document.fonts.ready; }")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin=margin,
                tagged=True,
                outline=True,
            )
            page.close()
            print(f"  PDF: {pdf_path.name}")
        browser.close()


def build_cv(cv_data: dict, api_key: str, langs: list, html_only: bool,
             profiles_to_build: dict):
    """Build CVs for the given profiles and languages."""
    # Ensure docs/ and docs/static/ exist
    DOCS_DIR.mkdir(exist_ok=True)
    docs_static = DOCS_DIR / "static"
    docs_static.mkdir(exist_ok=True)
    for fname in ("styles.css", "ai-suite.js"):
        src = ROOT / "static" / fname
        if src.exists():
            shutil.copy2(src, docs_static / fname)

    all_jobs = []  # Collect {html, pdf} for batch PDF generation

    for profile_name, profile_data in profiles_to_build.items():
        outputs = get_outputs(profile_name)
        data = {**cv_data, "profile": profile_data}

        label = f" [{profile_name}]" if profile_name != "default" else ""
        print(f"Generating CV HTML files...{label}")

        for lang in langs:
            if lang not in outputs:
                continue
            pdf_filename = outputs[lang]["pdf"]
            html = render_cv(data, lang, api_key, pdf_filename, profile_name)
            output_path = ROOT / outputs[lang]["html"]
            output_path.write_text(html, encoding="utf-8")
            print(f"  HTML: {output_path.name}")
            all_jobs.append(outputs[lang])

    if not html_only and all_jobs:
        print("Generating CV PDF files...")
        cv_margin = {"top": "0", "bottom": "0", "left": "0", "right": "0"}
        try:
            generate_pdfs(all_jobs, cv_margin)
            # Copy PDFs to docs/ for GitHub Pages download button
            for files in all_jobs:
                pdf_src = ROOT / files["pdf"]
                pdf_dst = DOCS_DIR / files["pdf"]
                if pdf_src.exists():
                    shutil.copy2(pdf_src, pdf_dst)
                    print(f"  Copy: docs/{files['pdf']}")
        except Exception as e:
            _handle_pdf_error(e)


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
        letter_margin = {"top": "0", "bottom": "0", "left": "0", "right": "0"}
        letter_jobs = [
            {"html": COVER_LETTER_OUTPUTS[l]["html"], "pdf": COVER_LETTER_OUTPUTS[l]["pdf"]}
            for l in langs
        ]
        try:
            generate_pdfs(letter_jobs, letter_margin)
        except Exception as e:
            _handle_pdf_error(e)


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
    # Generate sitemap.xml and robots.txt for SEO
    base_url = cv_data.get("personal", {}).get("portfolio", {}).get("url", "")
    if base_url:
        pages = ["index.html", "projects.html", "contact.html",
                 "CV_español.html", "CV_english.html"]
        sitemap_entries = "\n".join(
            f"  <url><loc>{base_url}{page}</loc></url>" for page in pages
        )
        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_entries}
</urlset>"""
        (DOCS_DIR / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
        print("  Generated: docs/sitemap.xml")
        robots_txt = f"User-agent: *\nAllow: /\nSitemap: {base_url}sitemap.xml\n"
        (DOCS_DIR / "robots.txt").write_text(robots_txt, encoding="utf-8")
        print("  Generated: docs/robots.txt")
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
    all_profiles = cv_data.get("profiles", {})

    # Extract --profile flag (None = build all profiles)
    profile_name = None
    if "--profile" in sys.argv:
        idx = sys.argv.index("--profile")
        if idx + 1 < len(sys.argv):
            profile_name = sys.argv[idx + 1]

    # Determine which profiles to build
    if profile_name:
        if profile_name not in all_profiles:
            available = ", ".join(all_profiles.keys())
            print(f"Warning: profile '{profile_name}' not found (available: {available})")
            print("Using default profile.")
            profile_name = "default"
        profiles_to_build = {profile_name: all_profiles[profile_name]}
        print(f"Using profile: {profile_name}")
    else:
        profiles_to_build = all_profiles

    args = [a for a in sys.argv[1:] if not a.startswith("--") and a != profile_name]

    # uv run python build.py carta [carta-es|carta-en]
    if "carta" in args or "carta-es" in args or "carta-en" in args:
        cv_data["profile"] = all_profiles.get("default", {})
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
        cv_data["profile"] = all_profiles.get("default", {})
        build_portfolio(cv_data)
        print("\nDone!")
        return

    # uv run python build.py [es|en] [--html-only] [--profile name]
    langs = ["es", "en"]
    if args and args[0] in ("es", "en"):
        langs = [args[0]]

    build_cv(cv_data, api_key, langs, html_only, profiles_to_build)
    print("\nDone!")


if __name__ == "__main__":
    main()
