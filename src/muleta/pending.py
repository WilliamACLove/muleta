"""Pending queue — proposed jargon terms awaiting human approval.

Novel-jargon proposals (from the client LLM or the watchlist) land here, never in the
scored corpus, until a human approves them. Keeps the corpus trustworthy and reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "pending_terms.yaml"


@dataclass
class PendingEntry:
    term: str
    example: str = ""
    reason: str = ""
    source: str = "llm-suggested"
    count: int = 1


class PendingQueue:
    def __init__(self, entries: list[PendingEntry], path: Path):
        self._by_term = {e.term.lower(): e for e in entries}
        self.path = path

    @classmethod
    def load(cls, path: Path | str | None = None) -> "PendingQueue":
        p = Path(path) if path else _DEFAULT_PATH
        entries: list[PendingEntry] = []
        if p.exists():
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            for r in raw.get("entries", []):
                entries.append(
                    PendingEntry(
                        term=str(r["term"]),
                        example=str(r.get("example", "")),
                        reason=str(r.get("reason", "")),
                        source=str(r.get("source", "llm-suggested")),
                        count=int(r.get("count", 1)),
                    )
                )
        return cls(entries, p)

    def entries(self) -> list[PendingEntry]:
        return list(self._by_term.values())

    def get(self, term: str) -> PendingEntry | None:
        return self._by_term.get(term.lower())

    def propose(self, term: str, example: str = "", reason: str = "", source: str = "llm-suggested") -> PendingEntry:
        key = term.lower()
        e = self._by_term.get(key)
        if e:
            e.count += 1
            if example and not e.example:
                e.example = example
            if reason and not e.reason:
                e.reason = reason
        else:
            e = PendingEntry(term=term, example=example, reason=reason, source=source)
            self._by_term[key] = e
        return e

    def remove(self, term: str) -> None:
        self._by_term.pop(term.lower(), None)

    def save(self, path: Path | str | None = None) -> None:
        p = Path(path) if path else self.path
        rows = [
            {"term": e.term, "example": e.example, "reason": e.reason, "source": e.source, "count": e.count}
            for e in self._by_term.values()
        ]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            yaml.safe_dump({"entries": rows}, sort_keys=False, allow_unicode=True, width=4000),
            encoding="utf-8",
        )
