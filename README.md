# Muleta

**Muleta** detects business jargon and scores writing clarity. It is a faithful revival
of Deloitte Consulting's discontinued **Bullfighter** (2003–2005) — using the *actual*
recovered word list and the *actual* scoring formula — delivered as an **MCP server** any
LLM client can call. Named for the *muleta*, the matador's small red cape used to guide
the bull, because this tool guides writing away from bull.

A deterministic engine is the source of truth: it computes the **Bull Composite Index**
(0–10, 10 = clearest) from a **Bull Index** (jargon frequency × severity) and an
**Adjusted Flesch** reading-ease score. The calling LLM does the explaining and rewriting,
grounded on those real numbers.

> The dictionary (113 headwords) and the scoring formula were recovered from the shipped
> Bullfighter 1.2 installer and the vendor's scorecard. See `docs/recovery-notes.md` and
> `PROVENANCE.md`. The words are individually uncopyrightable and are compiled here
> independently, with provenance cited.

## Install

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # Windows
# source .venv/bin/activate && pip install -e ".[dev]"   # POSIX
```

## Use as an MCP server

Register the server with any MCP client (Claude Desktop, Claude Code, etc.):

```json
{
  "mcpServers": {
    "muleta": {
      "command": "muleta-mcp"
    }
  }
}
```

| Tool | Purpose |
|------|---------|
| `score_text(text)` | Full report: Bull Composite, Bull Index (BI + raw), raw + adjusted Flesch, hits, versions |
| `find_jargon(text)` | Just the jargon hits, with Bull weight (1–10) and offsets |
| `corpus_list()` | List every corpus term with weight and provenance |
| `corpus_add(term, weight, source, note)` | Add a term (weight 1–10) to the corpus (persisted) |

## Use as a CLI

```bash
muleta score --text "Going forward, we will leverage our core competencies."
muleta score path/to/doc.docx --json
muleta corpus list
```

## Scoring — authentic Bullfighter (`bfc-v2`)

Recovered verbatim from the vendor scorecard. All three scores share a 0–10 scale
(10 = best), except raw Flesch which keeps its native scale.

- **Weight factor** `F` = 2 / 3 / 4 / 5 by document length (<1k / <10k / <50k / ≥50k words).
  F caps how many repeats of a term are penalized.
- **Bull Index** — each term has a Bull weight `Bᵢ` from 1 (an abused real word like
  "global") to 10 (worst coinage like "envisioneer"). For `Cᵢ` occurrences,
  `Wᵢ = min(Cᵢ/F, 1)`; `BIr = 100 − Σ(Bᵢ·Wᵢ)`; `BI = 0 if BIr<0 else BIr/10`. Aim for 90+.
- **Adjusted Flesch** — raw `F = 206.835 − (1.015·S + 84.6·L)`, then
  `AF = 10·CDF(F, μ=40, σ=25)` to weight for an educated readership.
- **Bull Composite** — `Pb = (15−√BI)/(30−√BI−√AF)`, `Pf` symmetric,
  `BCI = Pb·BI + Pf·AF`. The *worse* of the two components is weighted more heavily.

`FORMULA_VERSION` is `bfc-v2`; the earlier transparent approximation `bfc-v1` is kept in
the source for provenance. The formula is pinned by golden-file tests, so scores never
drift silently.

## The corpus is a living dataset

`data/jargon.yaml` is versioned, carries provenance per term (`extracted` /
`reconstructed` / `user` / `llm-suggested`), and its version is stamped into every score
(`corpus_version`) so results are reproducible.

## Develop

```bash
.venv/Scripts/ruff check src tests
.venv/Scripts/pytest -q
```
