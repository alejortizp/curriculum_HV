.PHONY: all build html es en carta setup clean open-es open-en open-carta help

# Default: build everything (HTML + PDF)
all: build

# Build HTML + PDF for both languages
build:
	uv run python build.py

# Build HTML only (no PDF)
html:
	uv run python build.py --html-only

# Build only Spanish
es:
	uv run python build.py es

# Build only English
en:
	uv run python build.py en

# Build cover letter (HTML + PDF)
carta:
	uv run python build.py carta

# First-time setup
setup:
	uv sync
	uv run playwright install chromium

# Remove generated files
clean:
	rm -f CV_español.html CV_english.html CV_español.pdf CV_english.pdf
	rm -f Carta_Presentacion.html Carta_Presentacion.pdf

# Open Spanish CV in default browser
open-es: html
	xdg-open CV_español.html 2>/dev/null || open CV_español.html 2>/dev/null || echo "Open CV_español.html manually"

# Open English CV in default browser
open-en: html
	xdg-open CV_english.html 2>/dev/null || open CV_english.html 2>/dev/null || echo "Open CV_english.html manually"

# Open cover letter in default browser
open-carta: carta
	xdg-open Carta_Presentacion.html 2>/dev/null || open Carta_Presentacion.html 2>/dev/null || echo "Open Carta_Presentacion.html manually"

# Show available targets
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build      Build HTML + PDF for both CV languages (default)"
	@echo "  html       Build HTML only (skip PDF)"
	@echo "  es         Build Spanish CV only (HTML + PDF)"
	@echo "  en         Build English CV only (HTML + PDF)"
	@echo "  carta      Build cover letter (HTML + PDF)"
	@echo "  setup      First-time setup (install dependencies)"
	@echo "  clean      Remove all generated HTML and PDF files"
	@echo "  open-es    Build HTML and open Spanish CV in browser"
	@echo "  open-en    Build HTML and open English CV in browser"
	@echo "  open-carta Build and open cover letter in browser"
	@echo "  help       Show this help"
