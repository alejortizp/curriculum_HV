"""Skills vocabulary: canonical names, aliases, general terms and skill state.

Canonical names come from cv.json -> tech_stack. data/skills_vocabulary.json adds
aliases and general terms; only the CV owner edits it, the model never does.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from textutil import plain, term_in

ROOT = Path(__file__).parent
VOCAB_FILE = ROOT / "data" / "skills_vocabulary.json"

COVERED, MENTIONED, GAP = "covered", "mentioned", "gap"


class VocabularyError(Exception):
    pass


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


@dataclass
class Vocabulary:
    names: list[str]
    cv_text: str
    alias_pairs: list[tuple[str, str]] = field(default_factory=list)   # (alias, canonical)
    general_terms: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self):
        self._aliases = {alias.lower(): target for alias, target in self.alias_pairs}
        known = self.names + list(self.general_terms)
        self._casing = {name.lower(): name for name in known}

    def _cased(self, name: str) -> str:
        return self._casing.get(name.strip().lower(), name.strip())

    def canonical(self, term: str, model_canonical: str | None = None) -> str:
        """Canonical name of a skill. The alias file wins over the model's answer."""
        for candidate in (term, model_canonical):
            if candidate and candidate.strip().lower() in self._aliases:
                return self._cased(self._aliases[candidate.strip().lower()])
        return self._cased(model_canonical or term)

    def forms(self, canonical: str) -> list[str]:
        """The canonical name plus every alias that points to it."""
        key = canonical.lower()
        return [canonical] + [alias for alias, target in self.alias_pairs if target.lower() == key]

    def backing(self, canonical: str) -> list[str]:
        """Skills that back a general term; empty for anything else."""
        return self.general_terms.get(self._cased(canonical), [])

    def state(self, canonical: str) -> str:
        backing = self.backing(canonical)
        if backing:
            states = {self.state(self.canonical(skill)) for skill in backing}
            return COVERED if COVERED in states else MENTIONED
        if canonical.lower() in {name.lower() for name in self.names}:
            return COVERED
        if any(term_in(form, self.cv_text) for form in self.forms(canonical)):
            return MENTIONED
        return GAP


def load(cv: dict, path: Path | None = None) -> Vocabulary:
    path = path or VOCAB_FILE
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    vocab = Vocabulary(
        names=[skill["name"] for cat in cv["tech_stack"] for line in cat["items"] for skill in line],
        cv_text=plain("\n".join(_strings(cv))),
        alias_pairs=list(data.get("aliases", {}).items()),
        general_terms=data.get("general_terms", {}),
    )
    for term, skills in vocab.general_terms.items():
        unbacked = [s for s in skills if Vocabulary.state(vocab, vocab.canonical(s)) == GAP]
        if not skills or unbacked:
            raise VocabularyError(
                f"El término general '{term}' no está respaldado por el CV: "
                f"{', '.join(unbacked) or 'sin habilidades declaradas'}."
            )
    return vocab
