"""Helpers shared by several test files. Import with `from helpers import ...`."""

import json

import vocabulary


def vocab(cv, tmp_path, aliases=None, general_terms=None):
    """A Vocabulary for `cv` built from a throwaway vocabulary file."""
    path = tmp_path / "vocab.json"
    path.write_text(json.dumps({"aliases": aliases or {}, "general_terms": general_terms or {}}))
    return vocabulary.load(cv, path)
