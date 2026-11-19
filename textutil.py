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


def term_in(term: str, text: str) -> bool:
    """True if `term` appears in `text` as a whole term, ignoring case.

    A match glued to a letter, a digit or a hyphen does not count, so "R" is not
    found in "R-1" or "RAG" and "Spark" is not found in "PySpark".
    """
    pattern = r"(?<![\w-])" + re.escape(term) + r"(?![\w-])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def numbers(text: str) -> set[str]:
    """Cifras de un texto, en la forma en que el validador las compara.

    El validador rechaza una viñeta si numbers(viñeta) no es subconjunto de
    numbers(original). Esta función decide qué tan estricta es esa regla.
    """
    # TODO(Alejandro): 5-10 líneas.
    raise NotImplementedError
