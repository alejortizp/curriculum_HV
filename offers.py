"""Repository for the job-offer history (see docs/adr/0001).

This is the only module that reads or writes offer files. Everything else asks
for offers through these functions and never builds a path inside offers_dir().
"""

import hashlib
import json
import os
from datetime import date
from pathlib import Path

from textutil import slugify_ascii

ROOT = Path(__file__).parent
PROVISIONAL = "-pendiente-"
_SLUG_MAX = 40


class OfferNotFound(Exception):
    pass


class EmptyOffer(Exception):
    pass


class DuplicateOffer(Exception):
    def __init__(self, existing_id: str):
        super().__init__(existing_id)
        self.existing_id = existing_id


def _dotenv(key: str) -> str:
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def offers_dir() -> Path:
    value = os.environ.get("OFFERS_DIR") or _dotenv("OFFERS_DIR")
    return Path(value).expanduser() if value else ROOT / "data" / "offers"


def _path(offer_id: str) -> Path:
    return offers_dir() / f"{offer_id}.json"


def _write(offer: dict) -> None:
    offers_dir().mkdir(parents=True, exist_ok=True)
    _path(offer["id"]).write_text(
        json.dumps(offer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _all() -> list[dict]:
    folder = offers_dir()
    if not folder.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]


def _final_id(added: str, company: str, role: str) -> str | None:
    """`AAAA-MM-DD-empresa-cargo`, or None when either part has no ASCII slug."""
    parts = [slugify_ascii(company)[:_SLUG_MAX].strip("-"), slugify_ascii(role)[:_SLUG_MAX].strip("-")]
    return f"{added}-{parts[0]}-{parts[1]}" if all(parts) else None


def _unique(base: str) -> str:
    candidate, n = base, 1
    while _path(candidate).exists():
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def add(raw_text: str, *, company: str = "", role: str = "", url: str = "",
        today: date | None = None) -> dict:
    text = raw_text.strip()
    if not text:
        raise EmptyOffer("El texto de la oferta está vacío.")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    for existing in _all():
        if existing["raw"]["sha256"] == sha:
            raise DuplicateOffer(existing["id"])

    added = (today or date.today()).isoformat()
    base = _final_id(added, company, role) or f"{added}{PROVISIONAL}{sha[:8]}"
    offer = {
        "id": _unique(base),
        "added": added,
        "company": company.strip(),
        "role": role.strip(),
        "url": url.strip(),
        "status": None,
        "raw": {"text": text, "sha256": sha},
        "extraction": None,
    }
    _write(offer)
    return offer


def get(offer_id: str) -> dict:
    path = _path(offer_id)
    if not path.exists():
        raise OfferNotFound(offer_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_offers(*, family: str | None = None, since: date | None = None) -> list[dict]:
    result = []
    for offer in _all():
        if family is not None and (offer["extraction"] or {}).get("role_family") != family:
            continue
        if since is not None and date.fromisoformat(offer["added"]) < since:
            continue
        result.append(offer)
    return sorted(result, key=lambda o: (o["added"], o["id"]))


def save_extraction(offer_id: str, extraction: dict) -> dict:
    """Store a (re)extraction. `raw` is never touched; `company`, `role` and a
    final id are only filled in when they were still missing."""
    offer = get(offer_id)
    offer["extraction"] = extraction
    offer["company"] = offer["company"] or extraction.get("company", "").strip()
    offer["role"] = offer["role"] or extraction.get("role", "").strip()

    if PROVISIONAL in offer_id:
        final = _final_id(offer["added"], offer["company"], offer["role"])
        if final:
            offer["id"] = _unique(final)
            _write(offer)
            _path(offer_id).unlink()
            return offer
    _write(offer)
    return offer
