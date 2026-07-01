# Installer Recovery Notes

Running log of attempts to recover the original Bullfighter dictionary and formula
constants from `bullfighter.exe` (a Wise Installation Wizard package). See
`tools/extract_installer.py`.

## Artifact identity

- `bullfighter.exe` / `bullfighter.zip` (identical payload, ~1.16 MB) — Wise
  installer. String markers: `WiseMain`, `Bullfighter 1.2 Installation`,
  `Initializing Wise Installation Wizard...`, `Could not extract Wise0132.dll`.

## Attempts (2026-07-01)

- **7-Zip (26.02) extraction:** FAILED — `Cannot open the file as archive`. Wise
  SFX is not a standard archive format 7-Zip can unpack.
- **Cleartext string scan for the dictionary:** NEGATIVE. 36,315 printable strings
  in the binary; probed for ~28 known bullwords/business-jargon terms (leverage,
  synergy, bandwidth, robust, paradigm, incentivize, value-added, …) — **zero
  matches**. The dictionary payload is compressed inside the Wise container, so it
  is not statically visible.
- **Formula constants (Flesch coefficients / severity tables):** not attempted —
  same compression barrier.

## Conclusion

Static recovery of the original ~350-word dictionary is **not possible** from the
installer without executing it. The word list lives inside the compressed Wise
payload (the installed Word/PowerPoint add-in DLL), not in cleartext.

**The only remaining route** is to run the 2004 installer in a disposable/VM
environment, let it drop the add-in, and inspect the installed DLL's resources for
the embedded dictionary and scoring constants. This is deferred to a deliberate,
user-initiated step — running a legacy unknown executable is a decision for the
repo owner, ideally inside a sandbox/VM.

## Fallback in effect

Per the design's graceful-fallback strategy, the **reconstructed seed corpus**
(`data/jargon.yaml`, all entries `source: reconstructed`) stands as the shipped
dictionary, and the transparent `bfc-v1` formula is used. If the DLL is later
recovered, extracted terms merge in via human review, tagged `source: extracted`,
bumping the corpus to `0.2.0` with a `CHANGELOG.md` entry — and golden score
literals are updated in the same commit if they shift.

`tools/extract_installer.py` remains as a re-runnable harness: if 7-Zip ever gains
Wise support or the add-in DLL is provided directly, point the tool at it to
auto-harvest candidate terms into `data/recovered_terms.yaml` for review.
