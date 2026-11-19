"""Text helpers shared by the offers pipeline. No third-party imports."""

import html as html_lib
import re
import unicodedata

_TAG = re.compile(r"<[^>]+>")
_TAG_NAME = re.compile(r"<\s*/?\s*([a-zA-Z][\w-]*)")


def slugify_ascii(text: str) -> str:
    """Filesystem-safe ASCII slug: accents and ñ are folded, symbols dropped."""
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^\w\s-]", "", folded.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


def plain(markup: str) -> str:
    """Visible text of an HTML fragment: tags removed, entities decoded."""
    return html_lib.unescape(_TAG.sub("", markup))


def tags(markup: str) -> set[str]:
    """Lower-cased names of the HTML tags used in a fragment."""
    return {name.lower() for name in _TAG_NAME.findall(markup)}


def fenced(text: str, tag: str = "offer") -> str:
    """Untrusted text wrapped in <tag>…</tag>. Any closing tag of its own is removed,
    repeatedly, so the text cannot end the fence early and pose as instructions
    (removing "</offer>" from "</of</offer>fer>" would otherwise leave a new one)."""
    closing = re.compile(rf"<\s*/\s*{tag}[^>]*>", re.IGNORECASE)
    cleaned = text
    while closing.search(cleaned):
        cleaned = closing.sub("", cleaned)
    return f"<{tag}>\n{cleaned}\n</{tag}>"


def term_in(term: str, text: str) -> bool:
    """True if `term` appears in `text` as a whole term, ignoring case.

    A match glued to a letter, a digit or a hyphen does not count, so "R" is not
    found in "R-1" or "RAG" and "Spark" is not found in "PySpark".
    """
    pattern = r"(?<![\w-])" + re.escape(term) + r"(?![\w-])"
    return re.search(pattern, text, re.IGNORECASE) is not None


_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text: str) -> set[str]:
    """Figures in a text, in the form the validator compares them.

    Bare digits, without units or symbols: "10k+" and "10 k" are both {"10"}, so a
    harmless rewording is not rejected. The price is that "10k" -> "10" is not
    caught either; that is left to the human review of the adjustments file.
    Decimals stay whole and a decimal comma equals a decimal point.
    """
    return {match.replace(",", ".") for match in _NUMBER.findall(text)}
