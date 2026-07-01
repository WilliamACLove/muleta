"""Watchlist — deterministic detection of suspected jargon NOT in the scored corpus.

Independently compiled from public-domain / permissive sources (plainlanguage.gov,
GOV.UK, business-press buzzword lists). Matches here are *candidates*: surfaced for
review and possible promotion into the scored corpus, never scored themselves.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from muleta.corpus import Corpus

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "watchlist.yaml"


@dataclass(frozen=True)
class Candidate:
    term: str
    suggestions: tuple[str, ...]
    source: str
    start: int
    end: int


@dataclass(frozen=True)
class WatchEntry:
    term: str
    suggestions: tuple[str, ...]
    source: str


class Watchlist:
    def __init__(self, version: str, entries: list[WatchEntry]):
        self.version = version
        self._entries = entries

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Watchlist":
        p = Path(path) if path else _DEFAULT_PATH
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        entries = [
            WatchEntry(str(r["term"]), tuple(r.get("suggestions", []) or ()), str(r.get("source", "")))
            for r in raw["entries"]
        ]
        return cls(str(raw["version"]), entries)

    def entries(self) -> list[WatchEntry]:
        return list(self._entries)

    def scan(self, text: str, corpus: Corpus) -> list[Candidate]:
        """Return watchlist matches whose lemma is not already in the scored corpus."""
        found: list[Candidate] = []
        for e in self._entries:
            if corpus.weight(e.term) is not None:
                continue
            tokens = re.split(r"[ \-]+", e.term.strip())
            core = r"[ \-]+".join(re.escape(t) for t in tokens if t)
            pat = re.compile(r"(?<![A-Za-z])" + core + r"(?:s|es|ed|ing|d)?(?![A-Za-z])", re.IGNORECASE)
            for m in pat.finditer(text):
                found.append(Candidate(e.term, e.suggestions, e.source, m.start(), m.end()))
        found.sort(key=lambda c: c.start)
        return found
