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
    term: str
    severity: int
    source: str
    added: str
    notes: str = ""
    aliases: tuple[str, ...] = ()


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
                str(row["term"]),
                int(row["severity"]),
                str(row["source"]),
                str(row["added"]),
                str(row.get("notes", "")),
                tuple(row.get("aliases", []) or ()),
            )
            if not (1 <= e.severity <= 5):
                raise CorpusError(f"severity out of range for {e.term!r}")
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

    def severity(self, term: str) -> int | None:
        e = self._by_term.get(term.lower())
        return e.severity if e else None

    def add(self, term, severity, source, added, note="", aliases=()):
        if self.severity(term) is not None:
            raise CorpusError(f"term already exists: {term!r}")
        if not (1 <= int(severity) <= 5):
            raise CorpusError("severity must be 1..5")
        if source not in VALID_SOURCES:
            raise CorpusError(f"bad source: {source}")
        e = Entry(str(term), int(severity), str(source), str(added), str(note), tuple(aliases))
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
            row = {"term": e.term, "severity": e.severity, "source": e.source, "added": e.added}
            if e.notes:
                row["notes"] = e.notes
            if e.aliases:
                row["aliases"] = list(e.aliases)
            rows.append(row)
        Path(path).write_text(
            yaml.safe_dump({"version": self.version, "entries": rows}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
