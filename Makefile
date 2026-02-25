.PHONY: all build html es en carta carta-es carta-en portfolio setup clean open-es open-en open-carta open-carta-en open-portfolio help

# Profile variant for CV (e.g., make es PROFILE=ai-engineer). No flag = all profiles.
PROFILE_FLAG = $(if $(PROFILE),--profile $(PROFILE),)

# Default: build everything (all CV profiles + PDFs + portfolio)
all: build portfolio

# Build HTML + PDF for all profiles (or single profile with PROFILE=name)
build:
	uv run python build.py $(PROFILE_FLAG)

# Build HTML only (no PDF), all profiles
html:
	uv run python build.py --html-only $(PROFILE_FLAG)

# Build only Spanish (all profiles or PROFILE=name)
es:
	uv run python build.py es $(PROFILE_FLAG)

# Build only English (all profiles or PROFILE=name)
en:
	uv run python build.py en $(PROFILE_FLAG)

# Build cover letter (HTML + PDF) - both languages
carta:
	uv run python build.py carta

# Build cover letter - Spanish only
carta-es:
	uv run python build.py carta-es

# Build cover letter - English only
carta-en:
	uv run python build.py carta-en

# Build portfolio pages (GitHub Pages)
portfolio:
	uv run python build.py portfolio

# First-time setup
setup:
	uv sync
	uv run playwright install chromium

# Remove generated files (all profiles)
clean:
	rm -f docs/CV_español*.html docs/CV_english*.html
	rm -f docs/CV_español*.pdf docs/CV_english*.pdf docs/CV-*.pdf
	rm -f CV_español*.pdf CV_english*.pdf CV-*.pdf
	rm -rf docs/static
	rm -f Carta_Presentacion.html Carta_Presentacion.pdf
	rm -f Cover_Letter.html Cover_Letter.pdf
	rm -f docs/sitemap.xml docs/robots.txt

# Open Spanish CV in default browser
open-es: html
	xdg-open docs/CV_español.html 2>/dev/null || open docs/CV_español.html 2>/dev/null || echo "Open docs/CV_español.html manually"

# Open English CV in default browser
open-en: html
	xdg-open docs/CV_english.html 2>/dev/null || open docs/CV_english.html 2>/dev/null || echo "Open docs/CV_english.html manually"

# Open cover letter (Spanish) in default browser
open-carta: carta
	xdg-open Carta_Presentacion.html 2>/dev/null || open Carta_Presentacion.html 2>/dev/null || echo "Open Carta_Presentacion.html manually"

# Open cover letter (English) in default browser
open-carta-en: carta
	xdg-open Cover_Letter.html 2>/dev/null || open Cover_Letter.html 2>/dev/null || echo "Open Cover_Letter.html manually"

# Open portfolio in default browser
open-portfolio: portfolio
	xdg-open docs/index.html 2>/dev/null || open docs/index.html 2>/dev/null || echo "Open docs/index.html manually"

# Show available targets
help:
	@echo "Usage: make [target] [PROFILE=name]"
	@echo ""
	@echo "Targets:"
	@echo "  all        Build everything: all CV profiles + PDFs + portfolio (default)"
	@echo "  build      Build HTML + PDF for all profiles × both languages"
	@echo "  html       Build HTML only (skip PDF generation)"
	@echo "  es         Build Spanish CVs only (HTML + PDF)"
	@echo "  en         Build English CVs only (HTML + PDF)"
	@echo "  carta      Build cover letter (HTML + PDF, both languages)"
	@echo "  carta-es   Build cover letter - Spanish only"
	@echo "  carta-en   Build cover letter - English only"
	@echo "  portfolio  Build portfolio pages in docs/ (GitHub Pages)"
	@echo "  setup      First-time setup (install dependencies)"
	@echo "  clean      Remove all generated HTML and PDF files"
	@echo "  open-es    Build HTML and open Spanish CV in browser"
	@echo "  open-en    Build HTML and open English CV in browser"
	@echo "  open-carta Build and open cover letter (ES) in browser"
	@echo "  open-carta-en Build and open cover letter (EN) in browser"
	@echo "  open-portfolio Build and open portfolio in browser"
	@echo "  help       Show this help"
	@echo ""
	@echo "Options:"
	@echo "  PROFILE=name  Build only a specific profile (default, ai-engineer, ml-engineer, mlops)"
	@echo "                Example: make es PROFILE=ai-engineer"
	@echo "                Without PROFILE, all profiles are built."
