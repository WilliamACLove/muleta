"""Usage logging — local-only statistics on which jargon shows up in your writing.

On by default; logs to a local JSONL file and never transmits anything. Disable with the
env var MULETA_NO_USAGE=1. Override the path with MULETA_USAGE_PATH (used by tests).
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def enabled() -> bool:
    return os.environ.get("MULETA_NO_USAGE", "") not in ("1", "true", "yes")


def usage_path() -> Path:
    override = os.environ.get("MULETA_USAGE_PATH")
    return Path(override) if override else Path.home() / ".muleta" / "usage.jsonl"


def record(report) -> bool:
    """Append one line for a score. Returns False if logging is disabled."""
    if not enabled():
        return False
    p = usage_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "composite": report.composite,
        "word_count": report.word_count,
        "corpus_version": report.corpus_version,
        "hits": [h.term for h in report.hits],
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return True


def aggregate(path: Path | str | None = None) -> dict:
    """Aggregate the local usage log: per-term frequency, doc counts, and averages."""
    p = Path(path) if path else usage_path()
    if not p.exists():
        return {"documents": 0, "terms": [], "avg_composite": None}
    term_occurrences: Counter = Counter()
    term_docs: dict[str, int] = defaultdict(int)
    docs = 0
    composite_sum = 0.0
    for raw in p.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        rec = json.loads(raw)
        docs += 1
        composite_sum += float(rec.get("composite", 0.0))
        hits = rec.get("hits", [])
        for t in hits:
            term_occurrences[t] += 1
        for t in set(hits):
            term_docs[t] += 1
    terms = [
        {"term": t, "occurrences": term_occurrences[t], "documents": term_docs[t]}
        for t in sorted(term_occurrences, key=lambda x: (-term_occurrences[x], x))
    ]
    return {
        "documents": docs,
        "avg_composite": round(composite_sum / docs, 2) if docs else None,
        "terms": terms,
    }
