"""Build data/watchlist.yaml — suspected jargon NOT yet in the scored corpus.

Independently compiled from public-domain / permissive sources (US plainlanguage.gov,
GOV.UK words-to-avoid, and cross-source business-buzzword lists). Individual words are
uncopyrightable; we cite sources for provenance (see PROVENANCE.md). Entries whose lemma
already appears in the scored corpus are dropped, so the watchlist only adds new coverage.

Usage:  python tools/build_watchlist.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# term -> (plain suggestions, source tag)
# PD = plainlanguage.gov (US Gov, public domain); GOVUK = GOV.UK words-to-avoid (OGL);
# BUZZ = cross-source business-press buzzword lists (Forbes/LinkedIn/Preply/TechTarget).
PAIRS: dict[str, tuple[list[str], str]] = {
    # --- bureaucratic wordiness (plainlanguage.gov) ---
    "utilize": (["use"], "PD"), "utilise": (["use"], "PD"),
    "commence": (["begin", "start"], "PD"), "endeavor": (["try"], "PD"),
    "facilitate": (["help", "ease"], "PD"), "ascertain": (["find out", "learn"], "PD"),
    "accordingly": (["so"], "PD"), "additional": (["added", "more"], "PD"),
    "anticipate": (["expect"], "PD"), "apprise": (["tell", "inform"], "PD"),
    "commence": (["begin", "start"], "PD"), "component": (["part"], "PD"),
    "comprise": (["form", "include"], "PD"), "demonstrate": (["show", "prove"], "PD"),
    "disseminate": (["send", "give", "issue"], "PD"), "elucidate": (["explain"], "PD"),
    "endeavor": (["try"], "PD"), "expedite": (["speed up", "hasten"], "PD"),
    "expeditious": (["fast", "quick"], "PD"), "expend": (["spend"], "PD"),
    "finalize": (["finish", "complete"], "PD"), "forthwith": (["now", "at once"], "PD"),
    "furnish": (["give", "send"], "PD"), "henceforth": (["from now on"], "PD"),
    "heretofore": (["until now"], "PD"), "implement": (["carry out", "start"], "PD"),
    "inasmuch as": (["since"], "PD"), "indicate": (["show", "say"], "PD"),
    "initiate": (["start", "begin"], "PD"), "necessitate": (["cause", "need"], "PD"),
    "notwithstanding": (["despite", "still"], "PD"), "obtain": (["get"], "PD"),
    "peruse": (["read"], "PD"), "predicated on": (["based on"], "PD"),
    "prioritize": (["rank"], "PD"), "procure": (["buy", "get"], "PD"),
    "promulgate": (["issue", "publish"], "PD"), "pursuant to": (["under", "following"], "PD"),
    "remuneration": (["pay"], "PD"), "subsequent": (["later", "next"], "PD"),
    "sufficient": (["enough"], "PD"), "terminate": (["end", "stop"], "PD"),
    "thereafter": (["then", "after that"], "PD"), "therein": (["there"], "PD"),
    "aforementioned": (["this", "that", "these"], "PD"), "commensurate": (["equal", "matching"], "PD"),
    "cognizant": (["aware"], "PD"), "delineate": (["describe", "outline"], "PD"),
    "efficacious": (["effective"], "PD"), "eventuate": (["result", "happen"], "PD"),
    "exigent": (["urgent"], "PD"), "in lieu of": (["instead of"], "PD"),
    "in the event that": (["if"], "PD"), "methodology": (["method"], "PD"),
    "monetary": (["money"], "PD"), "numerous": (["many"], "PD"),
    "optimum": (["best"], "PD"), "parameters": (["limits", "boundaries"], "PD"),
    "predicate": (["base"], "PD"), "requisite": (["required", "needed"], "PD"),
    "utilization": (["use"], "PD"), "verbiage": (["wording", "text"], "PD"),
    "whereas": (["because", "since"], "PD"), "whilst": (["while"], "PD"),
    # --- GOV.UK words-to-avoid ---
    "deliver": (["make", "provide", "achieve"], "GOVUK"), "deploy": (["use", "put in place"], "GOVUK"),
    "dialogue": (["talk", "discussion"], "GOVUK"), "incentivise": (["encourage", "motivate"], "GOVUK"),
    "incentivize": (["encourage", "motivate"], "GOVUK"), "key": (["important"], "GOVUK"),
    "liaise": (["work with"], "GOVUK"), "tackle": (["deal with", "solve"], "GOVUK"),
    "transform": (["change"], "GOVUK"), "foster": (["encourage", "help"], "GOVUK"),
    "drive": (["cause", "encourage"], "GOVUK"), "combat": (["fix", "reduce"], "GOVUK"),
    "progress": (["develop", "work on"], "GOVUK"), "collaborate": (["work with"], "GOVUK"),
    "champion": (["support", "promote"], "GOVUK"), "embed": (["set up", "fix"], "GOVUK"),
    "slim down": (["reduce"], "GOVUK"), "one-stop shop": (["service", "website"], "GOVUK"),
    # --- modern buzzwords not in the Bullfighter corpus (business press) ---
    "circle back": (["follow up", "return to"], "BUZZ"), "move the needle": (["make a difference"], "BUZZ"),
    "deep dive": (["examine", "study"], "BUZZ"), "double click": (["look closer", "focus"], "BUZZ"),
    "take offline": (["discuss separately"], "BUZZ"), "put a pin in it": (["pause", "revisit later"], "BUZZ"),
    "ducks in a row": (["get organized"], "BUZZ"), "in the weeds": (["bogged down"], "BUZZ"),
    "boil the ocean": (["do too much"], "BUZZ"), "run it up the flagpole": (["test the idea"], "BUZZ"),
    "per my last email": (["as I said"], "BUZZ"), "table this": (["postpone"], "BUZZ"),
    "game changer": (["big improvement"], "BUZZ"), "north star": (["main goal"], "BUZZ"),
    "single source of truth": (["one reliable record"], "BUZZ"), "quick win": (["easy result"], "BUZZ"),
    "level up": (["improve"], "BUZZ"), "socialize": (["share", "discuss"], "BUZZ"),
    "operationalize": (["put into practice"], "BUZZ"), "headwinds": (["challenges"], "BUZZ"),
    "learnings": (["lessons"], "BUZZ"), "optics": (["appearance", "perception"], "BUZZ"),
    "cadence": (["rhythm", "schedule"], "BUZZ"), "swim lane": (["area of responsibility"], "BUZZ"),
    "wheelhouse": (["area of expertise"], "BUZZ"), "bake in": (["build in", "include"], "BUZZ"),
    "unpack": (["explain", "examine"], "BUZZ"), "granularity": (["detail"], "BUZZ"),
    "value-add": (["benefit"], "BUZZ"), "actionable": (["usable", "practical"], "BUZZ"),
}


def main() -> int:
    from muleta.corpus import Corpus

    corpus_terms = {t.lower() for t in Corpus.load().terms()}
    entries = []
    seen = set()
    for term, (sugg, src) in PAIRS.items():
        key = term.lower()
        if key in corpus_terms or key in seen:
            continue  # only add NEW coverage
        seen.add(key)
        entries.append({"term": term, "suggestions": sugg, "source": src})
    entries.sort(key=lambda e: e["term"])
    out = ROOT / "data" / "watchlist.yaml"
    out.write_text(
        yaml.safe_dump({"version": "0.1.0", "entries": entries}, sort_keys=False, allow_unicode=True, width=4000),
        encoding="utf-8",
    )
    print(f"wrote {len(entries)} watchlist entries to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
