# Corpus Changelog

## 1.1.0 — 2026-07-01
- **Clean read of the recovered Access `.mdb`** (via `access-parser`; the data pages are
  not encrypted). Replaces the lossy plaintext extraction with exact data:
  - **135 lemmas** with **exact Bull weights** straight from the DB (e.g. synergy=10,
    architect=9, bandwidth=5, best practice=1) — no longer tier-guessed.
  - **Explicit surface forms** per lemma (leveraged/leverages/leveraging), so matching is
    exact rather than regex-inflected.
  - **Clean replacement suggestions** (leverage → use, reuse; holistic → complete,
    comprehensive) — now surfaced by the engine, CLI, and MCP tools.
  - The original **"diagnosis" comments** carried per entry.
- Reproducible via `tools/build_corpus_from_mdb.py` (needs the `tools` extra). The `.mdb`
  itself is not distributed.

## 1.0.0 — 2026-07-01
- **Authentic dictionary.** 113 headwords recovered from the shipped Bullfighter 1.2
  installer (Wayback Machine capture of fightthebull.com → Wise-installer payload →
  embedded Microsoft Access `.mdb`). Replaces the reconstructed seed.
- Bull weights (1–10) assigned by tier, anchored to the vendor's confirmed values
  (`global`=1 abused real word; `leverage`=high; `envisioneer`=10 worst coinage).
  Exact per-word weights live in the `.mdb`'s binary column (password-protected) and
  remain future work.
- Replacement suggestions were recovered but omitted this release: the plaintext export
  concatenates DB columns without delimiters, corrupting ~15% of replacements. Clean
  replacements await a proper Jet `.mdb` read.

## 0.1.0 — 2026-07-01
- Seed corpus: reconstructed starter set (leverage, bandwidth, synergy, robust,
  value-added) from archived Bullfighter press coverage. **Superseded by 1.0.0.**
