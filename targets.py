"""What a derived CV is aimed at: one offer, or the market report of a role family.

Both kinds have the same shape, so one generator and one validator serve them.
"""

from report import build_report
from vocabulary import GAP, Vocabulary


class TargetError(Exception):
    pass


def _from_report(report: dict, cv: dict, vocab: Vocabulary) -> dict:
    """The part shared by both kinds: what to emphasize, what is backed, what is banned."""
    emphasize, gaps = [], []
    for skill in report["skills"]:          # already ordered by weight
        canonical = skill["canonical"]
        if skill["state"] == GAP:
            gaps.append({"canonical": canonical, "forms": vocab.forms(canonical)})
        elif not skill["backing"]:
            emphasize.append(canonical)
    # Every declared general term, requested or not: the rule that a general term must
    # sit next to a backing skill applies to all of them. Each backing skill is listed in
    # every way it may be written, so the validator finds "Databricks" when the
    # vocabulary name is "Databricks + MLflow".
    general_terms = {
        term: [form for backing in skills for form in vocab.forms(vocab.canonical(backing))]
        for term, skills in vocab.general_terms.items()
    }
    family = report["family"]
    return {
        "profile": family if family in cv["profiles"] else "default",
        "emphasize": emphasize,
        "general_terms": general_terms,
        "gaps": gaps,
        "responsibilities": [item for entry in report["responsibilities"] for item in entry["items"]],
    }


def from_offer(offer: dict, cv: dict, vocab: Vocabulary, lang: str | None = None) -> dict:
    extraction = offer.get("extraction")
    if not extraction:
        raise TargetError(f"La oferta {offer['id']} no tiene extracción. Ejecuta: make offers-extract")
    report = build_report([offer], extraction["role_family"], vocab)
    offer_lang = extraction.get("language")
    return {
        "kind": "offer",
        "id": offer["id"],
        "lang": lang or (offer_lang if offer_lang in ("es", "en") else "es"),
        **_from_report(report, cv, vocab),
        "context": {"company": offer["company"], "role": offer["role"]},
        "source_text": offer["raw"]["text"],
    }


def from_report(report: dict, cv: dict, vocab: Vocabulary, lang: str = "es") -> dict:
    if report["n_offers"] == 0:
        raise TargetError(f"No hay ofertas extraídas en la familia '{report['family']}'.")
    return {
        "kind": "family",
        "id": report["family"],
        "lang": lang,
        **_from_report(report, cv, vocab),
        "context": {"family": report["family"], "n_offers": report["n_offers"]},
        "source_text": None,
    }
