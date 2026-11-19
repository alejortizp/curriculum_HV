import pytest

import llm
import offers
import offers_cli
from helpers import GOOD, fake


def test_add_saves_raw_before_extracting(offers_dir, cv_file):
    def boom(*a, **k):
        raise llm.LLMError("sin red")
    with pytest.raises(llm.LLMError):
        offers_cli.cmd_add("texto de oferta", complete=boom)
    [pending] = offers.list_offers()
    assert pending["extraction"] is None and "-pendiente-" in pending["id"]


def test_add_extracts_and_finalizes_id(offers_dir, cv_file):
    offer = offers_cli.cmd_add("texto", complete=fake(GOOD))
    assert "-pendiente-" not in offer["id"] and offer["extraction"]["role_family"] == "data-engineer"


def test_company_parameter_wins_over_model(offers_dir, cv_file):
    assert offers_cli.cmd_add("texto", company="Mía", role="Rol", complete=fake(GOOD))["company"] == "Mía"


def test_extract_only_touches_pending_unless_forced(offers_dir, cv_file):
    offers_cli.cmd_add("uno", complete=fake(GOOD))
    assert offers_cli.cmd_extract(complete=fake()) == []
    assert len(offers_cli.cmd_extract(force=True, complete=fake(GOOD))) == 1


def test_list_command_prints_one_line_per_offer(offers_dir, cv_file, capsys):
    offer = offers_cli.cmd_add("uno", complete=fake(GOOD))
    offers_cli.main(["list"])
    out = capsys.readouterr().out
    assert offer["id"] in out and "data-engineer" in out and "Empresa Real" in out


def test_duplicate_is_reported_in_one_line_and_exits_1(offers_dir, cv_file, tmp_path, capsys):
    offer = offers.add("mismo texto", company="Acme", role="X")
    source = tmp_path / "oferta.txt"
    source.write_text("mismo texto")
    with pytest.raises(SystemExit) as exc:
        offers_cli.main(["add", "--file", str(source)])
    assert exc.value.code == 1 and offer["id"] in capsys.readouterr().out
