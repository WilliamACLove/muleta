from __future__ import annotations

import datetime as _dt
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from muleta import usage
from muleta.corpus import Corpus, _DEFAULT_PATH
from muleta.pending import PendingQueue
from muleta.report import score as _score
from muleta.watchlist import Watchlist

mcp = FastMCP("muleta")

# Overridable in tests; default to the packaged data.
CORPUS_PATH: Path = _DEFAULT_PATH
WATCHLIST_PATH: Path | None = None  # None -> packaged default
PENDING_PATH: Path | None = None  # None -> packaged default


# --- scoring (deterministic) ---

@mcp.tool()
def score_text(text: str) -> dict:
    """Score text with the authentic Bullfighter formula (bfc-v2). Returns the Bull
    Composite Index (0-10, 10=clearest), Bull Index (BI and raw BIr), raw + adjusted
    Flesch, word count, weight factor, jargon hits (term, weight, offsets, replacement
    suggestions), and versions. Logs the result to the local usage stats by default."""
    r = _score(text, Corpus.load(CORPUS_PATH))
    usage.record(r)
    return r.to_dict()


@mcp.tool()
def find_jargon(text: str) -> dict:
    """List jargon terms found in the text, with Bull weight (1-10), offsets, and
    plain-language replacement suggestions."""
    r = _score(text, Corpus.load(CORPUS_PATH))
    return {
        "count": len(r.hits),
        "hits": [
            {"term": h.term, "weight": h.weight, "start": h.start, "end": h.end,
             "suggestions": list(h.suggestions)}
            for h in r.hits
        ],
        "corpus_version": r.corpus_version,
    }


# --- novel-jargon detection + review pipeline ---

@mcp.tool()
def scan_candidates(text: str) -> dict:
    """Deterministically flag suspected jargon that is NOT yet in the scored corpus,
    using the watchlist (plain-language + buzzword sources). These are candidates for
    promotion, not scored. Each carries a plain-language suggestion and its source."""
    corpus = Corpus.load(CORPUS_PATH)
    wl = Watchlist.load(WATCHLIST_PATH)
    cands = wl.scan(text, corpus)
    return {
        "count": len(cands),
        "candidates": [
            {"term": c.term, "suggestions": list(c.suggestions), "source": c.source,
             "start": c.start, "end": c.end}
            for c in cands
        ],
    }


@mcp.tool()
def analyze(text: str) -> dict:
    """Full analysis for an LLM client: the deterministic score, the known jargon hits,
    and watchlist candidates not yet in the corpus. IMPORTANT for the calling model: read
    the text for ANY additional business jargon not listed in `hits` or `candidates`, and
    propose each new term with `propose_term(term, example, reason)`. Proposals go to a
    human-reviewed queue; they are never scored until approved with `approve_term`."""
    r = _score(text, Corpus.load(CORPUS_PATH))
    usage.record(r)
    corpus = Corpus.load(CORPUS_PATH)
    cands = Watchlist.load(WATCHLIST_PATH).scan(text, corpus)
    return {
        "score": r.to_dict(),
        "candidates": [
            {"term": c.term, "suggestions": list(c.suggestions), "source": c.source}
            for c in cands
        ],
        "instruction": (
            "Identify any business jargon in the text NOT already in score.hits or "
            "candidates, and call propose_term for each. Do not invent terms that aren't "
            "in the text."
        ),
    }


@mcp.tool()
def propose_term(term: str, example: str = "", reason: str = "") -> dict:
    """Propose a new jargon term for the corpus. Adds it to the human-review queue
    (never auto-scored). If already pending, increments its count. `example` = the phrase
    it appeared in; `reason` = why it is jargon."""
    q = PendingQueue.load(PENDING_PATH)
    e = q.propose(term, example=example, reason=reason)
    q.save()
    return {"ok": True, "term": e.term, "count": e.count, "status": "pending review"}


@mcp.tool()
def review_queue() -> dict:
    """List jargon terms proposed and awaiting human approval, with how often each has
    been proposed and the example that triggered it."""
    q = PendingQueue.load(PENDING_PATH)
    return {
        "count": len(q.entries()),
        "pending": [
            {"term": e.term, "count": e.count, "example": e.example, "reason": e.reason,
             "source": e.source}
            for e in q.entries()
        ],
    }


@mcp.tool()
def approve_term(term: str, weight: int, note: str = "") -> dict:
    """Approve a pending term into the scored corpus (weight 1-10) and remove it from the
    queue. This is the human-in-the-loop step; proposals never enter scoring without it."""
    q = PendingQueue.load(PENDING_PATH)
    e = q.get(term)
    src = e.source if e else "llm-suggested"
    c = Corpus.load(CORPUS_PATH)
    c.add(term, weight=weight, source=src, added=_dt.date.today().isoformat(), note=note)
    c.save(CORPUS_PATH)
    q.remove(term)
    q.save()
    return {"ok": True, "term": term, "weight": weight, "added_to": "corpus"}


# --- corpus management ---

@mcp.tool()
def corpus_list() -> dict:
    """List all jargon terms in the corpus with Bull weight (1-10) and provenance."""
    c = Corpus.load(CORPUS_PATH)
    return {
        "version": c.version,
        "count": len(c.entries()),
        "entries": [
            {"term": e.term, "weight": e.weight, "source": e.source} for e in c.entries()
        ],
    }


@mcp.tool()
def corpus_add(term: str, weight: int, source: str = "user", note: str = "") -> dict:
    """Add a jargon term directly to the corpus (persisted). weight 1-10; source
    defaults to 'user'. For LLM-proposed terms, prefer propose_term + approve_term."""
    c = Corpus.load(CORPUS_PATH)
    c.add(term, weight=weight, source=source, added=_dt.date.today().isoformat(), note=note)
    c.save(CORPUS_PATH)
    return {"ok": True, "term": term, "weight": weight, "source": source}


# --- usage statistics (local-only) ---

@mcp.tool()
def usage_stats() -> dict:
    """Local usage statistics: how often each jargon term has appeared across the
    documents you have scored, plus how often pending (not-yet-approved) terms show up —
    evidence for whether a candidate is worth adding. Nothing is transmitted."""
    stats = usage.aggregate()
    pending_terms = {e.term.lower() for e in PendingQueue.load(PENDING_PATH).entries()}
    stats["pending_prevalence"] = [
        t for t in stats.get("terms", []) if t["term"].lower() in pending_terms
    ]
    stats["logging_enabled"] = usage.enabled()
    return stats


def run() -> None:
    """Console entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    run()
