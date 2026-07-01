# Installer Recovery Notes — SUCCESS

The original Bullfighter dictionary and scoring formula were **successfully recovered**
from primary sources. Muleta ships as a faithful restoration, not a reconstruction.

## What was recovered

1. **The dictionary (113 headwords)** — pulled from the shipped program's own Microsoft
   Access database, embedded inside the installer.
2. **The scoring formula** — Bull Index, Adjusted Flesch, and Bull Composite Index,
   transcribed verbatim from the vendor's scorecard page. Implemented as `bfc-v2`.

## How (the working method)

- The installer (`bullfighter.exe`, Wise Installation Wizard, Business Idiots LLC for
  Deloitte Consulting) was fetched from the Wayback Machine:
  `http://web.archive.org/web/20051214215751id_/http://www.fightthebull.com/bullfighter/bullfighter.zip`
- The Wise payload is a sequence of **raw DEFLATE streams** (zlib `decompressobj(-15)`,
  offset scan). Carving yielded ~24 streams: several nested PE files (the add-in DLLs)
  plus **one `Standard Jet DB` (.mdb)** holding the dictionary.
- The `.mdb` is **password-protected** (ACE OLEDB rejects it), but Jet stores text as
  **UTF-16LE**, so the bullwords, replacements, and jokey comments are directly readable.
  DB schema: `bullword`, `ownerword` (variant), `weight` (1–10), `suggestions`,
  `comments`, `score`, `type`, `diagnosis`, `codename`.

> A first local attempt (this repo, `tools/extract_installer.py` against the local
> Downloads copy) failed because it used 7-Zip (which cannot open Wise SFX) and a
> coarse boundary sweep that missed the raw-deflate streams. The successful method above
> is the raw-deflate offset carve on the Wayback copy.

## Formula (recovered verbatim → implemented as bfc-v2)

- **F (weight factor):** 2 if N<1000; 3 if 1000≤N<10000; 4 if 10000≤N<50000; 5 if N≥50000.
- **Bull Index:** Wᵢ = min(Cᵢ/F, 1); BIr = 100 − Σ(Bᵢ·Wᵢ); BI = 0 if BIr<0 else BIr/10.
- **Adjusted Flesch:** F = 206.835 − (1.015·S + 84.6·L); AF = CDF(F, μ=40, σ=25),
  scaled ×10 to share the 0–10 range (our documented interpretation for composite math).
- **Bull Composite:** Pb=(15−√BI)/(30−√BI−√AF), Pf symmetric; BCI = Pb·BI + Pf·AF.
  The worse of the two components is weighted more heavily.

Source: `http://web.archive.org/web/20090625004413/http://www.fightthebull.com:80/bullscorecard.asp`

## Clean read (resolved)

The `.mdb` reads cleanly with **`access-parser`** (pure Python) — the data pages are not
encrypted, only the Access UI password is set. This yielded the full table
`bull_kuzu_warshawsky_1` (356 rows): `weight` (exact 1–10), `ownerword` (lemma),
`bullword` (surface form), `suggestions`, `comments`. Corpus **1.1.0** is built directly
from it (135 lemmas, exact weights, explicit forms, clean replacements, and the original
diagnosis comments) via `tools/build_corpus_from_mdb.py`. The earlier tier-assigned
weights and the lossy plaintext replacements are superseded.

## What is NOT redistributed

The proprietary installer and `.mdb` are **not** committed to this public repo. Only the
individual words (uncopyrightable) are used, in an independently compiled corpus with
provenance cited. See `PROVENANCE.md`.
