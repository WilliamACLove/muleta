# Installer Recovery Notes

Running log of attempts to recover the original Bullfighter dictionary and formula
constants from `Bullfighter.exe` (a Wise Installation Wizard package). See
`tools/extract_installer.py`.

## Artifact identity

- `bullfighter.exe` / `bullfighter.zip` (identical payload) — Wise installer,
  string markers: `WiseMain`, `Bullfighter 1.2 Installation`,
  `Initializing Wise Installation Wizard...`.

## Attempts

- **7-Zip extraction:** _pending run_ — `python tools/extract_installer.py`.
- **String harvest for the ~350-word dictionary:** _pending_.
- **Formula constants (Flesch coefficients / severity tables):** _pending_.

## Outcome

If clean extraction fails, the reconstructed seed corpus (`data/jargon.yaml`,
`source: reconstructed`) stands, and the `bfc-v1` formula documented in the plan is
used. Any extracted terms are merged only after human review and bump the corpus to
`0.2.0` with a `CHANGELOG.md` entry.
