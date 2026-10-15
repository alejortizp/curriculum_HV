#!/usr/bin/env python3
"""Build script: generates CV, cover letter, and portfolio HTML files from templates + data."""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
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

# Portfolio language variants: {lang: file suffix}
PORTFOLIO_LANGS = {"es": "", "en": "_en"}

# Static assets copied next to generated HTML (docs/static, applications/<x>/static)
STATIC_ASSETS = ("styles.css", "ai-suite.js", "tailwind-cv.css", "tailwind-portfolio.css")

# Tailwind is compiled locally (no Play CDN): one CSS per theme, committed so builds
# still work offline. Pinned to v3 — the CDN served v3 and v4 changed the config format.
TAILWIND_VERSION = "v3.4.17"
TAILWIND_BUILDS = {"cv": "tailwind/cv.config.js", "portfolio": "tailwind/portfolio.config.js"}


def compile_tailwind() -> None:
    """Regenerate static/tailwind-<name>.css; on failure keep the committed CSS."""
    try:
        import pytailwindcss
    except ImportError:
        print("  Note: pytailwindcss not installed (uv sync --dev); using committed Tailwind CSS")
        return
    for name, config in TAILWIND_BUILDS.items():
        output = ROOT / "static" / f"tailwind-{name}.css"
        try:
            pytailwindcss.run(
                ["-c", config, "-i", "tailwind/input.css", "-o", str(output), "--minify"],
                cwd=ROOT, auto_install=True, version=TAILWIND_VERSION,
            )
            print(f"  CSS: static/{output.name}")
        except Exception as e:
            print(f"  Warning: Tailwind build failed for {name} ({e}); using committed {output.name}")


def copy_static_assets(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for fname in STATIC_ASSETS:
        src = ROOT / "static" / fname
        if src.exists():
            shutil.copy2(src, dest / fname)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_jinja_env: Environment | None = None

# Symbols that older ATS parsers mangle or drop; mapped to plain ASCII equivalents.
ATS_REPLACEMENTS = {
    "→": " -> ", "≥": ">=", "≤": "<=", "−": "-", "–": "-", "—": "-",
    "·": "-", " ": " ", "“": '"', "”": '"', "‘": "'", "’": "'",
}


def ats_text(value) -> str:
    text = str(value)
    for symbol, plain in ATS_REPLACEMENTS.items():
        text = text.replace(symbol, plain)
    return text


def get_jinja_env() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
        _jinja_env.globals["current_year"] = datetime.now().year
        _jinja_env.filters["ats"] = ats_text
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


def add_pdf_metadata(pdf_path: Path, title: str, author: str, subject: str = "",
                     keywords: str = "") -> None:
    """Inject metadata and drop blank trailing pages produced by the renderer."""
    try:
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(pdf_path)
        # clone_from keeps the catalog (structure tree, /Lang, outline); copying pages
        # one by one into a blank writer silently produced untagged PDFs
        writer = PdfWriter(clone_from=reader)
        blank = [i for i, page in enumerate(reader.pages) if not page.extract_text().strip()]
        for i in reversed(blank):
            del writer.pages[i]
        metadata = {
            "/Title": title,
            "/Author": author,
            "/Subject": subject or "Curriculum Vitae",
            "/Creator": "curriculum_HV build system",
        }
        if keywords:
            metadata["/Keywords"] = keywords
        writer.add_metadata(metadata)
        with open(pdf_path, "wb") as f:
            writer.write(f)
    except ImportError:
        pass  # pypdf not installed, skip metadata


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


def apply_profile_overrides(cv_data: dict, profile_name: str) -> dict:
    """Return cv_data with `profile_overrides[profile_name]` applied.

    Supported keys: `title` (replaces personal.title) and `experience`
    ({company: {lang: [bullets]}}, replaces that entry's bullets per language).
    Unknown company names raise, so a typo can't silently ship the base bullets.
    """
    overrides = cv_data.get("profile_overrides", {}).get(profile_name)
    if not overrides:
        return cv_data
    data = {**cv_data}
    if "title" in overrides:
        data["personal"] = {**data["personal"], "title": overrides["title"]}
    exp_overrides = overrides.get("experience", {})
    companies = {exp["company"] for exp in data["experience"]}
    unknown = set(exp_overrides) - companies
    if unknown:
        raise ValueError(f"profile_overrides.{profile_name}: unknown companies {sorted(unknown)}")
    data["experience"] = [
        {**exp, "items": {**exp["items"], **exp_overrides[exp["company"]]}}
        if exp["company"] in exp_overrides else exp
        for exp in data["experience"]
    ]
    return data


def build_cv(cv_data: dict, api_key: str, langs: list, html_only: bool,
             profiles_to_build: dict):
    """Build CVs for the given profiles and languages."""
    DOCS_DIR.mkdir(exist_ok=True)
    copy_static_assets(DOCS_DIR / "static")

    all_jobs = []  # Collect {html, pdf} for batch PDF generation
    author = cv_data.get("personal", {}).get("name", "")

    for profile_name, profile_data in profiles_to_build.items():
        outputs = get_outputs(profile_name)
        data = {**apply_profile_overrides(cv_data, profile_name), "profile": profile_data}

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
            # Add metadata and copy PDFs to docs/
            for files in all_jobs:
                pdf_src = ROOT / files["pdf"]
                if pdf_src.exists():
                    add_pdf_metadata(pdf_src, f"{author} — CV", author)
                    pdf_dst = DOCS_DIR / files["pdf"]
                    shutil.copy2(pdf_src, pdf_dst)
                    print(f"  Copy: docs/{files['pdf']}")
        except Exception as e:
            _handle_pdf_error(e)


ATS_DIR = ROOT / "ats"
ATS_TEMPLATE = "cv_ats.html"
ATS_MARGIN = {"top": "1.4cm", "bottom": "1.4cm", "left": "1.6cm", "right": "1.6cm"}


def get_ats_outputs(profile_name: str, lang: str) -> dict:
    """ATS file names follow the Firstname_Lastname_CV convention recruiters expect."""
    names = {"default": "", "ai-engineer": "AI-Engineer", "ml-engineer": "ML-Engineer", "mlops": "MLOps"}
    label = names.get(profile_name, profile_name)
    label = f"_{label}" if label else ""
    stem = f"Alejandro_Ortiz_Perdomo_CV{label}_{lang.upper()}"
    return {"html": f"ats/{stem}.html", "pdf": f"ats/{stem}.pdf"}


def build_ats(cv_data: dict, langs: list, html_only: bool, profiles_to_build: dict):
    """Build single-column, ATS-parseable CVs (no CDN, icons or multi-column layout)."""
    ATS_DIR.mkdir(exist_ok=True)
    env = get_jinja_env()
    template = env.get_template(ATS_TEMPLATE)
    author = cv_data["personal"]["name"]
    jobs = []

    print("Generating ATS CV HTML files...")
    for profile_name, profile_data in profiles_to_build.items():
        data = {**apply_profile_overrides(cv_data, profile_name), "profile": profile_data}
        keywords = ", ".join(
            skill["name"] for cat in data["tech_stack"] for line in cat["items"] for skill in line
        )
        for lang in langs:
            outputs = get_ats_outputs(profile_name, lang)
            (ROOT / outputs["html"]).write_text(template.render(cv=data, lang=lang), encoding="utf-8")
            print(f"  HTML: {outputs['html']}")
            jobs.append({**outputs, "title": f"{author} - {ats_text(data['personal']['title'])}",
                         "keywords": keywords})

    if html_only:
        return
    print("Generating ATS CV PDF files...")
    try:
        generate_pdfs(jobs, ATS_MARGIN)
    except Exception as e:
        _handle_pdf_error(e)
    for job in jobs:
        add_pdf_metadata(ROOT / job["pdf"], job["title"], author,
                         subject="Curriculum Vitae", keywords=job["keywords"])


def build_cover_letter(cv_data: dict, html_only: bool, langs: list | None = None):
    if langs is None:
        langs = list(COVER_LETTER_OUTPUTS.keys())

    if not COVER_LETTER_FILE.exists():
        print(f"  Cover letter data not found: {COVER_LETTER_FILE}")
        sys.exit(1)

    letter_data = load_json(COVER_LETTER_FILE)
    author = cv_data.get("personal", {}).get("name", "")

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
            for l in langs:
                pdf_path = ROOT / COVER_LETTER_OUTPUTS[l]["pdf"]
                if pdf_path.exists():
                    subject = "Carta de Presentación" if l == "es" else "Cover Letter"
                    add_pdf_metadata(pdf_path, f"{author} — {subject}", author, subject)
        except Exception as e:
            _handle_pdf_error(e)


def build_portfolio(cv_data: dict):
    DOCS_DIR.mkdir(exist_ok=True)
    copy_static_assets(DOCS_DIR / "static")
    env = get_jinja_env()
    print("Generating portfolio pages...")
    for lang, suffix in PORTFOLIO_LANGS.items():
        other_suffix = "_en" if lang == "es" else ""
        for page_name, config in PORTFOLIO_TEMPLATES.items():
            template = env.get_template(config["template"])
            base = config["output"].removesuffix(".html")
            output_name = f"{base}{suffix}.html"
            html = template.render(
                cv=cv_data, active_page=page_name, lang=lang,
                page_suffix=suffix, other_page_suffix=other_suffix,
            )
            output_path = DOCS_DIR / output_name
            output_path.write_text(html, encoding="utf-8")
            print(f"  HTML: docs/{output_name}")
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
        pages = [
            "index.html", "index_en.html",
            "projects.html", "projects_en.html",
            "contact.html", "contact_en.html",
            "CV_español.html", "CV_english.html",
        ]
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build CV, cover letter, and portfolio HTML/PDF files."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        choices=["es", "en", "carta", "carta-es", "carta-en", "portfolio", "ats", "ats-en"],
        help="Build target (default: all CV profiles in both languages)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Skip PDF generation, generate HTML only",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Build a specific CV profile (e.g., ai-engineer, ml-engineer, mlops)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = get_api_key()
    cv_data = load_json(DATA_FILE)
    all_profiles = cv_data.get("profiles", {})

    # Determine which profiles to build
    if args.profile:
        if args.profile not in all_profiles:
            available = ", ".join(all_profiles.keys())
            print(f"Warning: profile '{args.profile}' not found (available: {available})")
            print("Using default profile.")
            args.profile = "default"
        profiles_to_build = {args.profile: all_profiles[args.profile]}
        print(f"Using profile: {args.profile}")
    else:
        profiles_to_build = all_profiles

    target = args.target

    # Every target except the ATS CV (inline CSS) uses the compiled Tailwind CSS
    if target not in ("ats", "ats-en"):
        print("Compiling Tailwind CSS...")
        compile_tailwind()

    # Cover letter targets
    if target in ("carta", "carta-es", "carta-en"):
        cv_data["profile"] = all_profiles.get("default", {})
        carta_langs = list(COVER_LETTER_OUTPUTS.keys())
        if target == "carta-es":
            carta_langs = ["es"]
        elif target == "carta-en":
            carta_langs = ["en"]
        build_cover_letter(cv_data, args.html_only, carta_langs)
        print("\nDone!")
        return

    # Portfolio target
    if target == "portfolio":
        cv_data["profile"] = all_profiles.get("default", {})
        build_portfolio(cv_data)
        print("\nDone!")
        return

    # ATS-optimized CV targets (Spanish by default)
    if target in ("ats", "ats-en"):
        build_ats(cv_data, ["en" if target == "ats-en" else "es"], args.html_only, profiles_to_build)
        print("\nDone!")
        return

    # CV targets (default)
    langs = ["es", "en"]
    if target in ("es", "en"):
        langs = [target]

    build_cv(cv_data, api_key, langs, args.html_only, profiles_to_build)
    print("\nDone!")


if __name__ == "__main__":
    main()
