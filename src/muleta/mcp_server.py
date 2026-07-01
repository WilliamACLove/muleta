from __future__ import annotations

import datetime as _dt
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from muleta.corpus import Corpus, _DEFAULT_PATH
from muleta.report import score as _score

mcp = FastMCP("muleta")

# Overridable in tests; defaults to the packaged corpus.
CORPUS_PATH: Path = _DEFAULT_PATH


@mcp.tool()
def score_text(text: str) -> dict:
    """Score text for jargon and readability. Returns Bull Composite (1-10, 10=clearest),
    Bull Index, Flesch Reading Ease, word count, jargon hits with offsets, and versions."""
    return _score(text, Corpus.load(CORPUS_PATH)).to_dict()


@mcp.tool()
def find_jargon(text: str) -> dict:
    """List jargon terms found in the text, with severity and character offsets."""
    r = _score(text, Corpus.load(CORPUS_PATH))
    return {
        "count": len(r.hits),
        "hits": [
            {"term": h.term, "severity": h.severity, "start": h.start, "end": h.end}
            for h in r.hits
        ],
        "corpus_version": r.corpus_version,
    }


@mcp.tool()
def corpus_list() -> dict:
    """List all jargon terms in the corpus with severity and provenance."""
    c = Corpus.load(CORPUS_PATH)
    return {
        "version": c.version,
        "entries": [
            {"term": e.term, "severity": e.severity, "source": e.source} for e in c.entries()
        ],
    }


@mcp.tool()
def corpus_add(term: str, severity: int, source: str = "user", note: str = "") -> dict:
    """Add a jargon term to the corpus (persisted). severity 1-5; source defaults to 'user'."""
    c = Corpus.load(CORPUS_PATH)
    c.add(term, severity=severity, source=source, added=_dt.date.today().isoformat(), note=note)
    c.save(CORPUS_PATH)
    return {"ok": True, "term": term, "severity": severity, "source": source}


def run() -> None:
    """Console entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    run()
