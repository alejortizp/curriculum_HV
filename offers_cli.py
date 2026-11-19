#!/usr/bin/env python3
"""Command line for the job-offer history: add, extract, list, report."""

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

import build
import extraction
import llm
import offers
import report
import session
import vocabulary

# Prompts and answers of pending extractions, when a session answers them (not committed)
INBOX_DIR = build.ROOT / "applications" / "_inbox"


def _context() -> tuple[dict, vocabulary.Vocabulary]:
    # Loaded per call so the commands always see the current cv.json
    cv = build.load_json(build.DATA_FILE)
    return cv, vocabulary.load(cv)


def _extract_one(offer: dict, cv: dict, vocab, complete) -> dict:
    exchange_dir = INBOX_DIR / offer["id"]
    # default provider: a Claude Code session answering through files in the inbox
    complete, attempts = (complete, 2) if complete else session.provider(exchange_dir, "extraction")
    extracted = extraction.extract(offer["raw"]["text"], cv, vocab, complete=complete, attempts=attempts)
    saved = offers.save_extraction(offer["id"], extracted)
    shutil.rmtree(exchange_dir, ignore_errors=True)
    return saved


def cmd_add(text: str, *, company: str = "", role: str = "", url: str = "", complete=None) -> dict:
    # The raw text is saved first: if extraction fails or waits, the offer is not lost
    offer = offers.add(text, company=company, role=role, url=url)
    cv, vocab = _context()
    return _extract_one(offer, cv, vocab, complete)


def cmd_extract(*, force: bool = False, complete=None, waiting: list | None = None,
                failed: list | None = None) -> list[dict]:
    """Extract pending offers: those without an extraction and those with a prompt
    still open in the inbox (a forced re-extraction answered in session). Steps
    waiting for an answer go to `waiting` and invalid answers to `failed`, when
    given, so one offer does not stop the rest."""
    def open_step(offer):
        return (INBOX_DIR / offer["id"] / "extraction.prompt.md").exists()

    pending = [o for o in offers.list_offers() if force or o["extraction"] is None or open_step(o)]
    if not pending:
        return []
    cv, vocab = _context()
    updated = []
    for offer in pending:
        try:
            updated.append(_extract_one(offer, cv, vocab, complete))
        except session.AwaitingResponse as e:
            if waiting is None:
                raise
            waiting.append(e)
        except (session.SessionError, extraction.ExtractionError) as e:
            if failed is None:
                raise
            failed.append(e)
    return updated


def cmd_list() -> list[dict]:
    return offers.list_offers()


def cmd_report(family: str | None = None, since: date | None = None,
               out_root: Path | None = None) -> list[Path]:
    """Write report.json and report.md per family; returns the Markdown paths."""
    cv, vocab = _context()
    known = extraction.role_families(cv)
    if family and family not in known:
        raise ValueError(f"Familia desconocida: {family}. Opciones: {', '.join(known)}")
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


def _print_waiting(step: session.AwaitingResponse) -> None:
    if step.discarded:
        print(f"Nota: había una respuesta para un prompt anterior; quedó en {step.discarded.name}.")
    print(f"En una sesión de Claude Code, para {step.prompt_path.parent.name}:")
    print(f"  1. Lee {step.prompt_path.relative_to(build.ROOT)}")
    print(f"  2. Escribe la respuesta JSON en {step.response_path.relative_to(build.ROOT)}")
    print("  3. Ejecuta: make offers-extract")


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
            try:
                text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
            except UnicodeDecodeError:
                print(f"Error: {args.file} no está en UTF-8. Guárdalo como UTF-8 y vuelve a intentar.")
                sys.exit(1)
            print("Oferta registrada:\n  " + _describe(
                cmd_add(text, company=args.company, role=args.role, url=args.url)))
        elif args.command == "extract":
            waiting: list = []
            failed: list = []
            updated = cmd_extract(force=args.force, waiting=waiting, failed=failed)
            print(f"Ofertas extraídas: {len(updated)}")
            for offer in updated:
                print("  " + _describe(offer))
            for step in waiting:
                _print_waiting(step)
            for error in failed:
                print(f"Error: {error}")
            if failed:
                sys.exit(1)
        elif args.command == "list":
            listed = cmd_list()
            print("\n".join(_describe(o) for o in listed) if listed else "No hay ofertas registradas.")
        elif args.command == "report":
            paths = cmd_report(args.family, args.since)
            print("\n".join(f"Informe: {p}" for p in paths) if paths else "No hay ofertas extraídas.")
    except session.AwaitingResponse as e:
        print("Oferta guardada. Falta su extracción.")
        _print_waiting(e)
    except offers.DuplicateOffer as e:
        print(f"Esa oferta ya está registrada: {e.existing_id}")
        sys.exit(1)
    except (offers.EmptyOffer, offers.OfferNotFound, llm.LLMError, extraction.ExtractionError,
            session.SessionError, vocabulary.VocabularyError, offers.CorruptOffer, ValueError,
            OSError) as e:
        print(f"Error: {e}")
        if isinstance(e, (llm.LLMError, extraction.ExtractionError)):
            print("El texto quedó guardado; reintenta con: make offers-extract")
        sys.exit(1)


if __name__ == "__main__":
    main()
