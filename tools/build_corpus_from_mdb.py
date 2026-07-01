"""Rebuild data/jargon.yaml from the recovered Bullfighter Access .mdb.

The .mdb is a research artifact and is NOT distributed with this repo (it is the
vendor's proprietary database). This script documents how the shipped corpus was
produced and lets a holder of the .mdb regenerate it. The individual words, weights,
and replacements are uncopyrightable and compiled here independently (see PROVENANCE.md).

Usage:
    python tools/build_corpus_from_mdb.py path/to/RECOVERED_bullwords.mdb [-o data/jargon.yaml]

Requires the optional 'tools' extra:  pip install -e ".[tools]"   (adds access-parser)
"""
from __future__ import annotations

import argparse
import re
from collections import OrderedDict
from pathlib import Path

import yaml

TABLE = "bull_kuzu_warshawsky_1"
TERM_OK = re.compile(r"[A-Za-z][A-Za-z '\-]*$")


def build(mdb_path: str) -> dict:
    from access_parser import AccessParser  # imported lazily; needs the 'tools' extra

    db = AccessParser(mdb_path)
    t = db.parse_table(TABLE)
    n = len(t["ownerword"])

    groups: "OrderedDict[str, dict]" = OrderedDict()
    for i in range(n):
        lemma = (t["ownerword"][i] or "").strip()
        form = (t["bullword"][i] or "").strip()
        if not lemma or not TERM_OK.match(lemma):
            continue
        g = groups.setdefault(lemma, {"weight": None, "forms": set(), "suggestions": [], "comment": ""})
        try:
            g["weight"] = int(t["weight"][i])
        except (TypeError, ValueError):
            pass
        if form and TERM_OK.match(form):
            g["forms"].add(form)
        if t["suggestions"][i]:
            for s in str(t["suggestions"][i]).split(","):
                s = s.strip()
                if s and s not in g["suggestions"]:
                    g["suggestions"].append(s)
        if t["comments"][i] and not g["comment"]:
            g["comment"] = str(t["comments"][i]).strip()

    entries = []
    for lemma, g in groups.items():
        if g["weight"] is None:
            continue
        forms = sorted(f for f in g["forms"] if f.lower() != lemma.lower())
        e = {"term": lemma, "weight": g["weight"], "source": "extracted", "added": "2026-07-01"}
        if forms:
            e["forms"] = forms
        if g["suggestions"]:
            e["suggestions"] = g["suggestions"]
        if g["comment"]:
            e["comment"] = g["comment"]
        entries.append(e)
    return {"version": "1.1.0", "entries": entries}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mdb")
    ap.add_argument("-o", "--out", default=str(Path(__file__).resolve().parents[1] / "data" / "jargon.yaml"))
    args = ap.parse_args()
    doc = build(args.mdb)
    Path(args.out).write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=4000), encoding="utf-8"
    )
    print(f"wrote {len(doc['entries'])} lemmas to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
