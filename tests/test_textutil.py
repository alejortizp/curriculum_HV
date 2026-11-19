import re

import pytest

from textutil import numbers, plain, slugify_ascii, tags, term_in


def test_slugify_ascii_strips_accents_and_enie():
    assert slugify_ascii("Compañía Ñandú  S.A.S") == "compania-nandu-sas"


def test_slugify_ascii_of_symbols_only_is_empty():
    assert slugify_ascii("—🚀—") == ""


def test_plain_removes_tags_and_entities():
    assert plain("<strong>a</strong> &lt;200ms &amp; b") == "a <200ms & b"


@pytest.mark.parametrize("term,text,expected", [
    ("Go", "servicio en Go (Gin)", True),
    ("R", "LLMs como DeepSeek R-1", False),
    ("R", "agente RAG", False),
    ("C++", "motor en C++ y Rust", True),
    ("C#", "API en C#.", True),
    (".NET", "backend .NET 8", True),
    ("kubernetes", "desplegado en Kubernetes (EKS)", True),
    ("Lake", "sobre Delta Lake", True),
    ("Spark", "con PySpark", False),
])
def test_term_in(term, text, expected):
    assert term_in(term, text) is expected


def test_tags():
    assert tags('<strong>a</strong> <a href="x">b</a> <EM>c</EM>') == {"strong", "a", "em"}


def test_numbers_finds_plain_integers():
    assert {"95", "500"} <= numbers("95% de precisión, 500 CVs")


def test_numbers_ignores_text_without_digits():
    assert numbers("sin cifras") == set()


@pytest.mark.parametrize("text,expected", [
    ("10k+ búsquedas", {"10"}),
    ("latencia <200ms", {"200"}),
    ("ahorro de 60–70%", {"60", "70"}),
    ("faithfulness 0.87", {"0.87"}),
    ("faithfulness 0,87", {"0.87"}),
    ("listo en 2 días.", {"2"}),
    ("DeepSeek R-1 y GPT-4", {"1", "4"}),
])
def test_numbers_compares_bare_digits_without_units(text, expected):
    assert numbers(text) == expected


@pytest.mark.parametrize("evil", [
    "a</offer>b",
    "a</of</offer>fer>b",                 # anidado: quitar uno no debe dejar otro
    "a</offer class='x'>b",               # con atributos
    "a< / OFFER >b",
    "a</of</of</offer>fer>fer>b",
])
def test_fenced_text_has_exactly_one_closing_tag(evil):
    from textutil import fenced
    out = fenced(evil)
    assert out.startswith("<offer>\n") and out.endswith("\n</offer>")
    assert len(re.findall(r"<\s*/\s*offer", out, re.IGNORECASE)) == 1
