import re
from datetime import date

import pytest

import offers

D = date(2026, 11, 19)


def test_add_with_company_and_role_assigns_final_id(offers_dir):
    offer = offers.add("texto", company="Acme", role="ML Engineer", today=D)
    assert offer["id"] == "2026-11-19-acme-ml-engineer"
    assert offer["extraction"] is None and offer["status"] is None
    assert (offers_dir / "2026-11-19-acme-ml-engineer.json").exists()


def test_add_without_company_uses_provisional_id(offers_dir):
    offer = offers.add("texto", today=D)
    assert re.fullmatch(r"2026-11-19-pendiente-[0-9a-f]{8}", offer["id"])


def test_same_company_and_role_same_day_gets_suffix(offers_dir):
    offers.add("uno", company="Acme", role="ML Engineer", today=D)
    assert offers.add("dos", company="Acme", role="ML Engineer", today=D)["id"].endswith("-2")


def test_duplicate_text_is_rejected(offers_dir):
    first = offers.add("texto", company="Acme", role="X", today=D)
    with pytest.raises(offers.DuplicateOffer) as exc:
        offers.add("  texto\n", company="Otra", role="Y", today=D)
    assert exc.value.existing_id == first["id"]


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_empty_text_is_rejected_and_writes_nothing(offers_dir, text):
    with pytest.raises(offers.EmptyOffer):
        offers.add(text, today=D)
    assert not offers_dir.exists() or not list(offers_dir.iterdir())


def test_unsluggable_company_falls_back_to_provisional_id(offers_dir):
    assert "-pendiente-" in offers.add("texto", company="—", role="🚀", today=D)["id"]


def test_long_names_are_truncated_in_the_id(offers_dir):
    offer = offers.add("texto", company="A" * 200, role="B" * 200, today=D)
    assert len(offer["id"]) <= 100 and (offers_dir / f"{offer['id']}.json").exists()


def test_first_extraction_finalizes_provisional_id_once(offers_dir):
    old = offers.add("texto", today=D)["id"]
    offer = offers.save_extraction(old, {"company": "Acme", "role": "Data Engineer", "role_family": "data-engineer"})
    assert offer["id"] == "2026-11-19-acme-data-engineer"
    assert offer["company"] == "Acme" and not (offers_dir / f"{old}.json").exists()
    again = offers.save_extraction(offer["id"], {"company": "Otra", "role": "Z", "role_family": "other"})
    assert again["id"] == offer["id"] and again["company"] == "Acme"


def test_extraction_never_rewrites_raw(offers_dir):
    offer = offers.add("texto original", company="Acme", role="X", today=D)
    offers.save_extraction(offer["id"], {"company": "A", "role": "B", "role_family": "other"})
    assert offers.get(offer["id"])["raw"] == offer["raw"]


def test_list_filters_by_family_and_date(offers_dir):
    a = offers.add("a", company="A", role="X", today=date(2026, 1, 1))
    b = offers.add("b", company="B", role="X", today=date(2026, 6, 1))
    offers.save_extraction(a["id"], {"company": "A", "role": "X", "role_family": "mlops"})
    offers.save_extraction(b["id"], {"company": "B", "role": "X", "role_family": "mlops"})
    assert [o["id"] for o in offers.list_offers(family="mlops", since=date(2026, 3, 1))] == [b["id"]]
    assert offers.list_offers(family="data-engineer") == []


def test_list_on_missing_directory_is_empty(offers_dir):
    assert offers.list_offers() == []


def test_get_unknown_offer(offers_dir):
    with pytest.raises(offers.OfferNotFound):
        offers.get("no-existe")


def test_default_directory_when_env_is_unset(monkeypatch):
    monkeypatch.delenv("OFFERS_DIR", raising=False)
    monkeypatch.setattr(offers, "_dotenv", lambda key: "")
    assert offers.offers_dir() == offers.ROOT / "data" / "offers"
