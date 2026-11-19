#!/usr/bin/env python3
"""Command line for the job-offer history: add, extract, list, report."""

import argparse
import sys
from datetime import date
from pathlib import Path

import build
import extraction
import llm
import offers
import report
import vocabulary


def _context() -> tuple[dict, vocabulary.Vocabulary]:
    # Loaded per call so the commands always see the current cv.json
    cv = build.load_json(build.DATA_FILE)
    return cv, vocabulary.load(cv)


def cmd_add(text: str, *, company: str = "", role: str = "", url: str = "",
            complete=llm.complete_json) -> dict:
    # The raw text is saved first: if extraction fails, the offer is not lost
    offer = offers.add(text, company=company, role=role, url=url)
    cv, vocab = _context()
    extracted = extraction.extract(offer["raw"]["text"], cv, vocab, complete=complete)
    return offers.save_extraction(offer["id"], extracted)


def cmd_extract(*, force: bool = False, complete=llm.complete_json) -> list[dict]:
    pending = [o for o in offers.list_offers() if force or o["extraction"] is None]
    if not pending:
        return []
    cv, vocab = _context()
    return [
        offers.save_extraction(o["id"], extraction.extract(o["raw"]["text"], cv, vocab, complete=complete))
        for o in pending
    ]


def cmd_list() -> list[dict]:
    return offers.list_offers()


def cmd_report(family: str | None = None, since: date | None = None,
               out_root: Path | None = None) -> list[Path]:
    """Write report.json and report.md per family; returns the Markdown paths."""
    cv, vocab = _context()
    everything = offers.list_offers()
    families = [family] if family else sorted(
        {o["extraction"]["role_family"] for o in everything if o["extraction"]})
    out_root = out_root or report.MARKET_DIR
    return [
        report.write_report(report.build_report(everything, name, vocab, since), out_root / name)[1]
        for name in families
    ]


def _describe(offer: dict) -> str:
    family = (offer["extraction"] or {}).get("role_family", "pendiente")
    status = f" [{offer['status']}]" if offer["status"] else ""
    return f"{offer['id']}  |  {offer['company'] or '?'}  |  {offer['role'] or '?'}  |  {family}{status}"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Historial de ofertas de empleo.")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Registrar una oferta y extraer su estructura")
    add.add_argument("--file", help="Archivo con el texto de la oferta (por defecto, entrada estándar)")
    add.add_argument("--company", default="")
    add.add_argument("--role", default="")
    add.add_argument("--url", default="")

    extract = sub.add_parser("extract", help="Extraer las ofertas pendientes")
    extract.add_argument("--force", action="store_true", help="Volver a extraer todas")

    sub.add_parser("list", help="Listar las ofertas registradas")

    rep = sub.add_parser("report", help="Informe de mercado por familia de cargo")
    rep.add_argument("--family", help="Solo esta familia (por defecto, todas las que tengan ofertas)")
    rep.add_argument("--since", type=date.fromisoformat, help="Solo ofertas desde AAAA-MM-DD")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        if args.command == "add":
            text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
            print("Oferta registrada:\n  " + _describe(
                cmd_add(text, company=args.company, role=args.role, url=args.url)))
        elif args.command == "extract":
            updated = cmd_extract(force=args.force)
            print(f"Ofertas extraídas: {len(updated)}")
            for offer in updated:
                print("  " + _describe(offer))
        elif args.command == "list":
            listed = cmd_list()
            print("\n".join(_describe(o) for o in listed) if listed else "No hay ofertas registradas.")
        elif args.command == "report":
            paths = cmd_report(args.family, args.since)
            print("\n".join(f"Informe: {p}" for p in paths) if paths else "No hay ofertas extraídas.")
    except offers.DuplicateOffer as e:
        print(f"Esa oferta ya está registrada: {e.existing_id}")
        sys.exit(1)
    except (offers.EmptyOffer, offers.OfferNotFound, llm.LLMError, extraction.ExtractionError,
            vocabulary.VocabularyError, OSError) as e:
        print(f"Error: {e}")
        if isinstance(e, (llm.LLMError, extraction.ExtractionError)):
            print("El texto quedó guardado; reintenta con: make offers-extract")
        sys.exit(1)


if __name__ == "__main__":
    main()
