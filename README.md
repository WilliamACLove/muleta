# Muleta

**Muleta** detects business jargon and scores writing clarity. It is a revival of
Deloitte Consulting's discontinued **Bullfighter** (2003–2005), delivered as an
**MCP server** any LLM client can call. Named for the *muleta* — the matador's small
red cape, used to guide the bull — because this tool guides writing away from bull.

A deterministic engine is the source of truth: it computes a **Bull Composite**
(1–10, 10 = clearest) from a **Bull Index** (jargon frequency × severity, matched
against a versioned corpus) and **Flesch Reading Ease**. The calling LLM does the
explaining and rewriting, grounded on those real scores.

> Homage: the original scoring vocabulary (Bull Index, Bull Composite) is kept in
> tribute. See `docs/` for methodology and provenance.

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

Tools exposed:

| Tool | Purpose |
|------|---------|
| `score_text(text)` | Full report: Bull Composite, Bull Index, Flesch, hits, versions |
| `find_jargon(text)` | Just the jargon hits, with severity and offsets |
| `corpus_list()` | List every corpus term with severity and provenance |
| `corpus_add(term, severity, source, note)` | Add a term to the corpus (persisted) |

The client's own model handles explanation and rewriting, grounded on the
deterministic scores these tools return.

## Use as a CLI

```bash
muleta score --text "We must leverage synergy to win."
muleta score path/to/doc.docx --json
muleta corpus list
```

## The corpus is a living dataset

`data/jargon.yaml` is versioned, carries provenance per term (`extracted` /
`reconstructed` / `user` / `llm-suggested`), and is stamped into every score as
`corpus_version` so results are reproducible. Recover more of the original ~350-word
dictionary from the installer with `python tools/extract_installer.py` (best-effort,
human-reviewed).

## Scoring (bfc-v1)

- **Flesch Reading Ease** = `206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words)`
- **Bull Index** = `1000 × (Σ severity of hits) / word_count`
- **Bull Composite** = `round(1 + 9 × clamp(flesch/100) × (1 − clamp(bull_index/30)), 1)` → 1–10

The formula is versioned (`FORMULA_VERSION`) and pinned by golden-file tests, so
scores never drift silently.

## Develop

```bash
.venv/Scripts/ruff check src tests
.venv/Scripts/pytest -q
```
