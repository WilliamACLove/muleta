# Bullfighter Revival — Design Spec

**Date:** 2026-07-01
**Status:** Approved for planning
**Repo:** `bullfighter` (public GitHub, owner `WilliamACLove`); local working copy at `C:\Users\William\dev\bullfighter` (off the cloud mount).

---

## 1. Background

Bullfighter was Deloitte Consulting's anti-jargon tool (2003–2005, discontinued).
It installed a toolbar into Microsoft Word and PowerPoint and, working like
spell-check, flagged business jargon and scored documents for clarity. The
source artifact for this project is `Bullfighter.exe` (a Wise-packaged installer
for "Bullfighter 1.2"; the accompanying `.zip` contains the same executable).

**Original methodology (recovered from press + archived documentation):**

- **Bull Index** — frequency and severity of jargon, matched against a
  hand-built dictionary. Deloitte collected ~10,000 candidate "bullwords" from
  employees over nine months; ~350 made the shipped dictionary. Worst
  offenders included *leverage, bandwidth, synergy, robust, value-added*.
- **Flesch Reading Ease** — standard readability from sentence length and
  syllables per word.
- **Bull Composite Index** — a combined 1–10 clarity score (1 = poor,
  10 = excellent) blending the Bull Index and Flesch.

Original distribution site (`www.dc.com/bullfighter`) and the "Fight the Bull"
campaign are long dead. Part of this project's value is serving as the
**archival record** of the word list and method.

## 2. Goals & Guiding Principle

Revive Bullfighter's jargon-detection and readability scoring as a modern,
public, LLM-usable tool.

**Guiding principle:** the deterministic engine is the single source of truth.
The LLM never invents a score — it only *explains* the engine's findings and
*rewrites* prose, then re-scores its own rewrite through the engine to prove
improvement. Scoring works with no LLM at all; the LLM is strictly additive.

## 3. Core Approach (decided)

Deterministic engine as ground truth **+** an LLM layer on top. Not either/or.

## 4. Fidelity Strategy (decided: best-effort extraction, graceful fallback)

Two elements are reverse-engineered from the artifact, each with a documented
fallback. No rabbit-holing — try clean extraction, fall back if it isn't clean.

1. **Jargon dictionary + severity weights.**
   - *Primary:* unpack the Wise installer payload → recover the embedded word
     list and weights from the add-in DLL / data file.
   - *Fallback:* reconstruct from archived documentation and press coverage,
     each entry clearly marked `source: reconstructed` vs `source: extracted`.

2. **Bull Index → Bull Composite formula.**
   - The public record gives the ingredients (jargon frequency × severity;
     Flesch Reading Ease; 1–10 scale) but not the exact weighting.
   - *Primary:* attempt to recover constants from the binary.
   - *Fallback:* a transparent, documented **"Bullfighter-compatible"** formula,
     calibrated so known example documents land near their historical scores.
   - Either way the formula is **versioned and openly specified** — never a
     black box. Provenance (`extracted` vs `calibrated`) is documented.

## 5. Stack (decided)

Python. Best fit for the LLM layer, MCP server, contribution, and the user's
existing tooling ecosystem.

## 6. Architecture — Six Layers

```
bullfighter/                     public repo; local copy off the cloud mount
├─ bullfighter/                  LAYER 1 — core engine (pure Python, no LLM, no I/O)
│   ├─ text.py                   tokenizer, sentence splitter, syllable counter
│   ├─ flesch.py                 Flesch Reading Ease
│   ├─ bull_index.py             jargon matching + severity scoring
│   ├─ composite.py              Bull Composite (1–10)
│   └─ report.py                 structured result: scores + hit list w/ offsets
├─ data/
│   └─ jargon.yaml               LAYER 2 — versioned dictionary (word, severity,
│                                source, notes); the archival record
├─ cli/                          LAYER 3 — `bullfighter score|dejargon|extract`
├─ llm/                          LAYER 4 — provider-agnostic; Anthropic default
│   ├─ client.py                 thin provider abstraction (Claude default)
│   ├─ explain.py                why each hit is jargon, in context
│   ├─ rewrite.py                rewrite to raise score; engine-verified
│   └─ context_scan.py           catch jargon the fixed list misses
├─ mcp/                          LAYER 5 — thin MCP server: bull_score(), de_jargon()
├─ tools/
│   └─ extract_dll.py            installer/DLL extraction + dictionary recovery
├─ tests/                        unit tests + golden-file score fixtures
└─ docs/                         methodology writeup, provenance, this spec
```

**Layer 6 — Claude Code `/bullfighter` skill.** Wraps the CLI/MCP and installs
into `~/.claude/skills/`. Referenced from the repo (its source lives in the
repo under e.g. `skill/`), installed into the user's ecosystem separately.

### Unit boundaries (isolation)

- **Engine** (layer 1): pure functions, no I/O, no network. Input text →
  structured `Report`. Independently testable; the only thing that produces
  scores.
- **Dictionary** (layer 2): data, not code. Loadable/editable; carries
  provenance per entry.
- **CLI** (layer 3): I/O + file parsing (`.txt`, `.docx`, `.pptx`) around the
  engine. No scoring logic of its own.
- **LLM layer** (layer 4): consumes a `Report`, never computes scores. Rewrites
  are re-scored by the engine before being surfaced.
- **MCP** (layer 5): transport wrapper exposing engine + LLM functions as tools.
- **Skill** (layer 6): ergonomics wrapper for the user's Claude Code ecosystem.

## 7. Data Flow

```
text | .docx | .pptx
        │
        ▼
   ┌─────────┐      Report {
   │ ENGINE  │ ──▶    bull_index, flesch, composite (1–10),
   └─────────┘        hits: [{term, severity, start, end}], stats
        │
        ├── CLI prints Report (human / JSON)
        ├── MCP returns Report as JSON tool result
        └── LLM layer receives Report → explain / rewrite
                                          │
                                          ▼
                              rewrite re-scored by ENGINE;
                              surfaced only if composite improves
```

The `Report` object is the single contract every layer consumes.

## 8. LLM Layer Contract

- Provider-agnostic client; **defaults to Claude (Anthropic)**. Model IDs and
  params follow the current `claude-api` reference at build time.
- **Grounded outputs only:** explanations cite specific hits; rewrites are
  re-scored by the engine and surfaced only when the Bull Composite improves.
- LLM is never on the scoring path. Engine runs standalone without any API key.

## 9. Testing

- **Engine unit tests:** Flesch against known reference values; syllable
  counting; jargon matching (case, morphology, word boundaries); empty/edge
  inputs.
- **Golden-file tests:** sample documents with locked expected scores, so the
  formula cannot silently drift across changes.
- **Dictionary integrity:** schema validation on `jargon.yaml` (unique terms,
  valid severity range, provenance present).

## 10. Non-Goals (v1 — YAGNI)

- No Office add-in rebuild.
- No web app or GUI.
- No model fine-tuning.
- No non-English support.

These may follow once the engine is proven.

## 11. Hosting / Resumability

- Public GitHub repo under `WilliamACLove`, created via `gh` CLI (being
  installed; user does a one-time `gh auth login` interactively, then the repo
  is created and pushed).
- Local working copy on a real local path (`C:\Users\William\dev\bullfighter`)
  to avoid the cloud mount's known silent-write-drop behavior.
- The repo (git history + this spec) is the durable home; work resumes from the
  repo, not from any chat session.

## 12. Open Items Carried Into Planning

- Exact success threshold for "clean extraction" vs. fallback on the dictionary.
- Which document parsers to bundle for v1 CLI (`.txt`/`.docx`/`.pptx`).
- Calibration corpus for the Bullfighter-compatible formula (which historical
  example scores to target).
