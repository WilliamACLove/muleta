"""Investigative recovery tool for the original Bullfighter installer.

Attempts to unpack the Wise-packaged ``Bullfighter.exe`` and recover the embedded
jargon dictionary, writing a review draft to ``data/recovered_terms.yaml`` (every
entry tagged ``source: extracted``) for human approval before it enters the scored
corpus. Graceful fallback: if nothing is recoverable, it says so and exits 0 — the
seed corpus stands.

This is a best-effort helper, not a guaranteed extractor; the Wise format and the
add-in payload are only knowable by opening the binary. See docs/recovery-notes.md
for the running log of what worked.

Usage:
    python tools/extract_installer.py [path-to-Bullfighter.exe]
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_INSTALLER = Path.home() / "Downloads" / "bullfighter.exe"
OUT_DIR = Path(__file__).resolve().parents[1] / "build" / "extracted"
DRAFT = Path(__file__).resolve().parents[1] / "data" / "recovered_terms.yaml"

# Business-jargon seeds used to spot the embedded dictionary among extracted strings.
JARGON_HINTS = {
    "leverage", "synergy", "bandwidth", "robust", "paradigm", "incentivize",
    "value-added", "actionable", "holistic", "scalable", "empower", "mindshare",
    "deliverable", "core competency", "best practice", "touch base", "circle back",
}
_WORDISH = re.compile(r"^[A-Za-z][A-Za-z \-]{2,30}$")


def _try_7zip(installer: Path) -> bool:
    exe = shutil.which("7z") or shutil.which("7za")
    if not exe:
        print("[extract] 7-Zip not found on PATH; skipping archive extraction.")
        return False
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([exe, "x", "-y", f"-o{OUT_DIR}", str(installer)], capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"[extract] 7-Zip extracted payload to {OUT_DIR}")
        return True
    print("[extract] 7-Zip could not extract this installer (Wise payload may be opaque).")
    return False


def _harvest_candidate_terms() -> list[str]:
    """Scan extracted files for printable strings that look like jargon terms."""
    if not OUT_DIR.exists():
        return []
    found: set[str] = set()
    for f in OUT_DIR.rglob("*"):
        if not f.is_file():
            continue
        try:
            blob = f.read_bytes()
        except OSError:
            continue
        for chunk in re.split(rb"[^\x20-\x7e]+", blob):
            s = chunk.decode("ascii", "ignore").strip()
            if _WORDISH.match(s) and s.lower() in JARGON_HINTS:
                found.add(s.lower())
    return sorted(found)


def main(argv: list[str]) -> int:
    installer = Path(argv[1]) if len(argv) > 1 else DEFAULT_INSTALLER
    print(f"[extract] installer: {installer}")
    if not installer.exists():
        print("[extract] installer not found; nothing to do. Seed corpus stands.")
        return 0

    _try_7zip(installer)
    terms = _harvest_candidate_terms()
    if not terms:
        print("[extract] No dictionary terms recovered from the binary.")
        print("[extract] Fallback: keep the reconstructed seed corpus. Exit 0.")
        return 0

    lines = ['version: "0.0.0-draft"', "entries:"]
    for t in terms:
        lines += [f"  - term: {t}", "    severity: 3", "    source: extracted", '    added: "2026-07-01"']
    DRAFT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[extract] wrote {len(terms)} candidate terms to {DRAFT} for human review.")
    print("[extract] Review, set severities, then merge into data/jargon.yaml and bump the version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
