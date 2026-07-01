from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_SOURCES = {"extracted", "reconstructed", "user", "llm-suggested"}
_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "jargon.yaml"


class CorpusError(Exception):
    pass


@dataclass(frozen=True)
class Entry:
    term: str  # the lemma / base surface form
    weight: int  # Bull weight Bi, 1 (abused real word) .. 10 (worst coinage)
    source: str
    added: str
    forms: tuple[str, ...] = ()  # other surface forms to match (inflections/variants)
    suggestions: tuple[str, ...] = ()  # plain-language replacements
    comment: str = ""  # the original "diagnosis"
    notes: str = ""

    def surfaces(self) -> list[str]:
        """All matchable surface forms: the lemma plus its variants."""
        return [self.term, *self.forms]


class Corpus:
    def __init__(self, version: str, entries: list[Entry]):
        self.version = version
        self._entries = entries
        self._by_term = {e.term.lower(): e for e in entries}

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Corpus":
        p = Path(path) if path else _DEFAULT_PATH
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "version" not in raw or "entries" not in raw:
            raise CorpusError("corpus must have 'version' and 'entries'")
        entries: list[Entry] = []
        seen: set[str] = set()
        for row in raw["entries"]:
            e = Entry(
                term=str(row["term"]),
                weight=int(row["weight"]),
                source=str(row["source"]),
                added=str(row["added"]),
                forms=tuple(row.get("forms", []) or ()),
                suggestions=tuple(row.get("suggestions", []) or ()),
                comment=str(row.get("comment", "")),
                notes=str(row.get("notes", "")),
            )
            if not (1 <= e.weight <= 10):
                raise CorpusError(f"weight out of range (1..10) for {e.term!r}")
            if e.source not in VALID_SOURCES:
                raise CorpusError(f"bad source for {e.term!r}: {e.source}")
            key = e.term.lower()
            if key in seen:
                raise CorpusError(f"duplicate term: {e.term!r}")
            seen.add(key)
            entries.append(e)
        return cls(str(raw["version"]), entries)

    def terms(self) -> list[str]:
        return [e.term for e in self._entries]

    def entries(self) -> list[Entry]:
        return list(self._entries)

    def weight(self, term: str) -> int | None:
        e = self._by_term.get(term.lower())
        return e.weight if e else None

    def add(self, term, weight, source, added, note="", forms=(), suggestions=(), comment=""):
        if self.weight(term) is not None:
            raise CorpusError(f"term already exists: {term!r}")
        if not (1 <= int(weight) <= 10):
            raise CorpusError("weight must be 1..10")
        if source not in VALID_SOURCES:
            raise CorpusError(f"bad source: {source}")
        e = Entry(
            term=str(term),
            weight=int(weight),
            source=str(source),
            added=str(added),
            forms=tuple(forms),
            suggestions=tuple(suggestions),
            comment=str(comment),
            notes=str(note),
        )
        self._entries.append(e)
        self._by_term[e.term.lower()] = e

    def remove(self, term):
        key = term.lower()
        if key not in self._by_term:
            raise CorpusError(f"no such term: {term!r}")
        del self._by_term[key]
        self._entries = [e for e in self._entries if e.term.lower() != key]

    def save(self, path):
        rows = []
        for e in self._entries:
            row = {"term": e.term, "weight": e.weight, "source": e.source, "added": e.added}
            if e.forms:
                row["forms"] = list(e.forms)
            if e.suggestions:
                row["suggestions"] = list(e.suggestions)
            if e.comment:
                row["comment"] = e.comment
            if e.notes:
                row["notes"] = e.notes
            rows.append(row)
        Path(path).write_text(
            yaml.safe_dump({"version": self.version, "entries": rows}, sort_keys=False, allow_unicode=True, width=4000),
            encoding="utf-8",
        )
