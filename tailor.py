#!/usr/bin/env python3
"""Tailor CV and cover letter for a specific job offer using Claude API."""

import argparse
import copy
import json
import os
import re
import shutil
import sys
from pathlib import Path

from anthropic import Anthropic

from build import (
    ROOT,
    add_pdf_metadata,
    get_api_key,
    load_json,
    render_cover_letter,
    render_cv,
)

DATA_DIR = ROOT / "data"
JOB_OFFER_FILE = DATA_DIR / "job_offer.json"
CV_FILE = DATA_DIR / "cv.json"
APPLICATIONS_DIR = ROOT / "applications"


def get_anthropic_key() -> str:
    """Resolve ANTHROPIC_API_KEY from env var or .env file."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("Error: ANTHROPIC_API_KEY not found.")
        print("Set it in .env or as environment variable.")
        sys.exit(1)
    return key


def slugify(text: str) -> str:
    """Convert text to filesystem-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def company_label(company: str) -> str:
    """Convert company name to ASCII-safe label for PDF filenames."""
    _acronyms = {"ai", "ml", "mlops", "it", "sas", "ibm", "nae"}
    return "-".join(
        w.upper() if w.lower() in _acronyms else w.capitalize()
        for w in company.split()
    )


def build_tailoring_prompt(cv_data: dict, job_offer: dict, lang: str) -> str:
    """Build the prompt for Claude to tailor the CV and generate a cover letter."""
    lang_name = "Spanish" if lang == "es" else "English"
    num_exp = len(cv_data.get("experience", []))

    return f"""You are an expert career consultant. Tailor a CV and generate a cover letter for a specific job offer.

CRITICAL RULES:
- NEVER invent or fabricate experience, skills, or achievements
- ONLY reformulate, reorder, and emphasize what already exists in the CV data
- Keep all facts (dates, companies, metrics, numbers) exactly as they are
- You may rephrase bullet points to better highlight keywords from the job offer
- All output must be in {lang_name} ("{lang}")

## CV DATA (source of truth):
```json
{json.dumps(cv_data, ensure_ascii=False, indent=2)}
```

## JOB OFFER:
- Company: {job_offer.get('company', 'N/A')}
- Role: {job_offer.get('role', 'N/A')}
- Location: {job_offer.get('location', 'N/A')}
- Description: {job_offer.get('description', 'N/A')}
- Requirements: {json.dumps(job_offer.get('requirements', []), ensure_ascii=False)}
- Nice to have: {json.dumps(job_offer.get('nice_to_have', []), ensure_ascii=False)}
- Notes: {job_offer.get('notes', '')}

## YOUR TASK:
Return a JSON object with exactly this structure:
{{
  "chosen_profile": "<best matching profile from: default, ai-engineer, ml-engineer, mlops>",
  "tailored_summary": "<rewritten professional summary tailored to this offer, in {lang_name}. Use <strong> tags for key terms matching the offer. 3-4 sentences max. Based ONLY on real experience.>",
  "experience_order": [<indices 0 to {num_exp - 1} of experience entries, ordered by relevance to this offer. Most relevant first. Include ALL indices.>],
  "experience_bullets": {{
    "<index>": [<reordered AND/OR rephrased bullets for that experience entry in "{lang}". Keep all facts identical. Emphasize keywords from the offer. Only include entries that exist in "{lang}".>]
  }},
  "cover_letter": {{
    "recipient": "<appropriate recipient in {lang_name}>",
    "date": "<today's date formatted in {lang_name}>",
    "subject": "<application subject line>",
    "greeting": "<greeting>",
    "opening": "<compelling opening paragraph tailored to this company and role. May use <strong> for emphasis.>",
    "why_me_title": "<section title>",
    "why_me": ["<3-4 bullet points explaining fit, based ONLY on real experience. Use <strong> for emphasis.>"],
    "differentiator_title": "<section title>",
    "differentiator": "<what sets the candidate apart, based on real qualifications.>",
    "closing": "<closing paragraph>",
    "farewell": "<farewell>",
    "sign_off": "<sign off>"
  }}
}}

Return ONLY the JSON object. No markdown fences, no explanations."""


def call_claude(prompt: str, api_key: str) -> dict:
    """Call Claude API and parse the JSON response."""
    client = Anthropic(api_key=api_key)

    print("  Calling Claude API...")
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    # Remove markdown fences if present
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
    if response_text.endswith("```"):
        response_text = response_text.rsplit("```", 1)[0].strip()

    return json.loads(response_text)


def apply_tailoring(cv_data: dict, tailoring: dict, lang: str) -> tuple[dict, dict]:
    """Apply Claude's tailoring to cv_data. Returns (tailored_cv, cover_letter_data)."""
    tailored = copy.deepcopy(cv_data)

    # Apply tailored summary as the profile
    tailored["profile"] = {lang: tailoring["tailored_summary"]}

    # Reorder experience entries by relevance
    order = tailoring.get("experience_order", list(range(len(tailored["experience"]))))
    original_exp = tailored["experience"]
    tailored["experience"] = [original_exp[i] for i in order if i < len(original_exp)]

    # Apply rephrased/reordered bullets
    experience_bullets = tailoring.get("experience_bullets", {})
    for str_idx, bullets in experience_bullets.items():
        orig_idx = int(str_idx)
        # Find where this entry ended up after reordering
        if orig_idx in order:
            new_pos = order.index(orig_idx)
            entry = tailored["experience"][new_pos]
            if lang in entry.get("items", {}):
                entry["items"][lang] = bullets

    # Build cover letter data (i18n structure with single language)
    cl = tailoring["cover_letter"]
    cover_letter = {
        "company": cv_data.get("_job_company", ""),
        "recipient": {lang: cl.get("recipient", "")},
        "role": cv_data.get("_job_role", ""),
        "date": {lang: cl.get("date", "")},
        "subject": {lang: cl.get("subject", "")},
        "greeting": {lang: cl.get("greeting", "")},
        "opening": {lang: cl.get("opening", "")},
        "why_me_title": {lang: cl.get("why_me_title", "")},
        "why_me": {lang: cl.get("why_me", [])},
        "differentiator_title": {lang: cl.get("differentiator_title", "")},
        "differentiator": {lang: cl.get("differentiator", "")},
        "closing": {lang: cl.get("closing", "")},
        "farewell": {lang: cl.get("farewell", "")},
        "sign_off": {lang: cl.get("sign_off", "")},
    }

    return tailored, cover_letter


def generate_tailored_pdfs(output_dir: Path, html_pdf_pairs: list[tuple[Path, Path]]):
    """Generate PDFs from HTML files in the applications directory."""
    from playwright.sync_api import sync_playwright

    margin = {"top": "0", "bottom": "0", "left": "0", "right": "0"}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for html_path, pdf_path in html_pdf_pairs:
            page = browser.new_page()
            page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
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
            print(f"  PDF: {pdf_path.relative_to(ROOT)}")
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tailor CV and cover letter for a job offer using Claude API."
    )
    parser.add_argument(
        "--html-only", action="store_true", help="Skip PDF generation"
    )
    parser.add_argument(
        "--lang", type=str, default=None, help="Override language (es/en)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load job offer
    if not JOB_OFFER_FILE.exists():
        print(f"Error: {JOB_OFFER_FILE} not found.")
        print(
            "Copy data/job_offer_template.json to data/job_offer.json and fill it in."
        )
        sys.exit(1)

    job_offer = load_json(JOB_OFFER_FILE)
    cv_data = load_json(CV_FILE)

    company = job_offer.get("company", "").strip()
    role = job_offer.get("role", "").strip()
    if not company or not role:
        print("Error: job_offer.json must have 'company' and 'role' fields.")
        sys.exit(1)

    lang = args.lang or job_offer.get("lang", "es")
    if lang not in ("es", "en"):
        print(f"Error: lang must be 'es' or 'en', got '{lang}'")
        sys.exit(1)

    # Prepare output directory
    company_slug = slugify(company)
    output_dir = APPLICATIONS_DIR / company_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy static files so HTML can reference them
    static_dir = output_dir / "static"
    static_dir.mkdir(exist_ok=True)
    for fname in ("styles.css", "ai-suite.js"):
        src = ROOT / "static" / fname
        if src.exists():
            shutil.copy2(src, static_dir / fname)

    # Filenames
    author = cv_data.get("personal", {}).get("name", "")
    author_slug = author.replace(" ", "-")
    comp_label = company_label(company)
    lang_label = lang.upper()

    cv_pdf_name = f"CV-{author_slug}-{comp_label}-{lang_label}.pdf"
    carta_prefix = "Carta" if lang == "es" else "Cover-Letter"
    carta_pdf_name = f"{carta_prefix}-{author_slug}-{comp_label}-{lang_label}.pdf"

    print(f"\nTailoring CV for: {company} - {role} ({lang_label})")

    # Call Claude API
    anthropic_key = get_anthropic_key()
    cv_data["_job_company"] = company
    cv_data["_job_role"] = role
    prompt = build_tailoring_prompt(cv_data, job_offer, lang)
    tailoring = call_claude(prompt, anthropic_key)

    chosen_profile = tailoring.get("chosen_profile", "default")
    print(f"  Profile chosen: {chosen_profile}")

    # Apply tailoring
    tailored_cv, cover_letter_data = apply_tailoring(cv_data, tailoring, lang)
    cover_letter_data["company"] = company
    cover_letter_data["role"] = role

    # Generate CV HTML
    gemini_key = get_api_key()
    cv_html_name = f"CV-{company_slug}-{lang_label}.html"
    cv_html = render_cv(tailored_cv, lang, gemini_key, cv_pdf_name, chosen_profile)
    cv_html_path = output_dir / cv_html_name
    cv_html_path.write_text(cv_html, encoding="utf-8")
    print(f"  HTML: {cv_html_path.relative_to(ROOT)}")

    # Generate cover letter HTML
    carta_html_name = f"{carta_prefix}-{company_slug}-{lang_label}.html"
    carta_html = render_cover_letter(tailored_cv, cover_letter_data, lang)
    carta_html_path = output_dir / carta_html_name
    carta_html_path.write_text(carta_html, encoding="utf-8")
    print(f"  HTML: {carta_html_path.relative_to(ROOT)}")

    # Generate PDFs
    if not args.html_only:
        print("Generating PDFs...")
        try:
            pairs = [
                (cv_html_path, output_dir / cv_pdf_name),
                (carta_html_path, output_dir / carta_pdf_name),
            ]
            generate_tailored_pdfs(output_dir, pairs)

            # Add metadata
            cv_pdf_path = output_dir / cv_pdf_name
            if cv_pdf_path.exists():
                add_pdf_metadata(
                    cv_pdf_path, f"{author} - CV ({company})", author
                )
            carta_pdf_path = output_dir / carta_pdf_name
            if carta_pdf_path.exists():
                subject = "Carta de Presentacion" if lang == "es" else "Cover Letter"
                add_pdf_metadata(
                    carta_pdf_path,
                    f"{author} - {subject} ({company})",
                    author,
                    subject,
                )
        except Exception as e:
            print(f"\n  Error generating PDFs: {e}")
            print("  Make sure Playwright is installed: uv run playwright install chromium")
            sys.exit(1)

    # Save the tailoring result for reference
    tailoring_path = output_dir / "tailoring_result.json"
    tailoring_path.write_text(
        json.dumps(tailoring, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDone! Files in: {output_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
