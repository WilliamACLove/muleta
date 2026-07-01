# Bullfighter Phase 1 — MCP Server (Engine + Corpus + MCP) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Bullfighter as an **MCP server** — jargon detection + Flesch + Bull Composite (1–10) + a versioned, updatable corpus — exposed as MCP tools any LLM client can call, backed by a pure deterministic engine.

**Architecture:** A pure-Python core engine turns text into a structured `Report` (Bull Index, Flesch Reading Ease, Bull Composite, jargon hits with offsets, corpus version). An **MCP server** (FastMCP, stdio) exposes the engine and corpus as tools (`score_text`, `find_jargon`, `corpus_list`, `corpus_add`); the *calling* LLM does explanation/rewriting grounded on the deterministic scores. A lean CLI is retained for local testing and generating golden values. The jargon corpus is a versioned YAML dataset with provenance and a changelog.

**Tech Stack:** Python 3.11+, `mcp` (FastMCP) for the server, `pytest` (+ `anyio`), `pyyaml`, `python-docx`, `click` (CLI), `ruff` (lint). Packaged with `pyproject.toml`.

---

## File Structure

```
bullfighter/
├─ pyproject.toml                 packaging, deps, console_scripts (cli + mcp)
├─ README.md                      what/why, MCP client config, usage
├─ src/bullfighter/
│   ├─ __init__.py                version, public API re-exports
│   ├─ text.py                    tokenize words, split sentences, count syllables
│   ├─ flesch.py                  Flesch Reading Ease
│   ├─ corpus.py                  load / validate / version / mutate the dictionary
│   ├─ bull_index.py              jargon matching + severity → Bull Index
│   ├─ composite.py               Bull Composite (1–10), formula versioned
│   ├─ report.py                  Report dataclass (the single output contract)
│   ├─ parse.py                   read .txt / .docx into plain text
│   ├─ mcp_server.py             FastMCP server exposing engine + corpus tools
│   └─ cli.py                     lean CLI: `bullfighter score|corpus`
├─ data/
│   ├─ jargon.yaml                the corpus (seed + recovered)
│   └─ CHANGELOG.md               corpus change history
├─ tools/
│   └─ extract_installer.py       investigative recovery from Bullfighter.exe
└─ tests/
    ├─ test_text.py … test_parse.py
    ├─ test_mcp_server.py         MCP tool behavior (in-process)
    ├─ test_cli.py
    └─ golden/…                   locked expected scores
```

---

## Scoring Definitions (authoritative — tasks implement exactly these)

**Flesch Reading Ease:** `206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words)`.

**Bull Index:** `1000 × (Σ severity of hits) / word_count` (0 when no words). Higher = worse.

**Bull Composite (1–10, 10 = clearest)** — "Bullfighter-compatible v1":
- `flesch_norm = clamp(flesch / 100, 0, 1)`
- `jargon_penalty = clamp(bull_index / K_PENALTY, 0, 1)`, `K_PENALTY = 30.0`
- `composite01 = flesch_norm × (1 − jargon_penalty)`
- `composite = round(1 + 9 × composite01, 1)` → [1.0, 10.0]

`FORMULA_VERSION = "bfc-v1"`, constants in `composite.py`, pinned by golden tests.

---

### Task 0: Project scaffolding

**Files:** Create `pyproject.toml`, `src/bullfighter/__init__.py`, `README.md`, `tests/__init__.py`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "bullfighter"
version = "0.1.0"
description = "Revival of Deloitte's Bullfighter as an MCP server: jargon detection + readability scoring."
requires-python = ">=3.11"
dependencies = ["mcp>=1.10", "pyyaml>=6", "python-docx>=1.1", "click>=8.1"]

[project.optional-dependencies]
dev = ["pytest>=8", "anyio>=4", "ruff>=0.5"]

[project.scripts]
bullfighter = "bullfighter.cli:main"
bullfighter-mcp = "bullfighter.mcp_server:run"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Write `src/bullfighter/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Write minimal `README.md`**

```markdown
# Bullfighter (MCP)

A revival of Deloitte Consulting's discontinued Bullfighter (2003–2005): detect
business jargon and score writing clarity. A deterministic engine (Bull Index +
Flesch Reading Ease + Bull Composite 1–10) with a versioned, updatable jargon
corpus, delivered as an **MCP server** any LLM client can call. See `docs/` for
methodology and provenance. MCP client configuration lives below (added in the
MCP task).
```

- [ ] **Step 4: Create venv and install dev deps**

Run: `python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"`
Expected: installs bullfighter (+ mcp) editable, exit 0.

- [ ] **Step 5: Verify pytest discovers (no tests yet)**

Run: `.venv/Scripts/pytest -q`
Expected: "no tests ran" (exit 5).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/bullfighter/__init__.py README.md tests/__init__.py
git commit -m "chore: scaffold bullfighter MCP package"
```

---

### Task 1: Text utilities (words, sentences, syllables)

**Files:** Create `src/bullfighter/text.py`; Test `tests/test_text.py`.

- [ ] **Step 1: Write failing tests**

```python
from bullfighter.text import words, sentences, count_syllables

def test_words_basic():
    assert words("The cat sat.") == ["The", "cat", "sat"]

def test_words_keeps_hyphenates_drops_numbers():
    assert words("Well-being, synergy! 2026") == ["Well-being", "synergy"]

def test_sentences_splits_on_terminators():
    assert sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]

def test_sentences_single_no_terminator():
    assert sentences("no period here") == ["no period here"]

def test_count_syllables_common_words():
    assert count_syllables("cat") == 1
    assert count_syllables("table") == 2
    assert count_syllables("synergy") == 3
    assert count_syllables("leverage") == 3
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_text.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'bullfighter.text'`

- [ ] **Step 3: Implement `text.py`**

```python
import re

_WORD_RE = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")
_SENT_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")

def words(text: str) -> list[str]:
    """Alphabetic tokens (hyphenated words kept whole); numbers dropped."""
    return _WORD_RE.findall(text)

def sentences(text: str) -> list[str]:
    """Split on ., !, ? runs. A trailing fragment counts as one sentence."""
    return [s.strip() for s in _SENT_RE.findall(text) if s.strip()]

def count_syllables(word: str) -> int:
    """Heuristic: vowel groups minus common silent trailing 'e'. Locked by tests."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    count = len(_VOWEL_GROUP_RE.findall(w))
    if w.endswith("e") and not w.endswith(("le", "ie", "ee", "ye")) and count > 1:
        count -= 1
    return max(count, 1)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_text.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/text.py tests/test_text.py
git commit -m "feat: text tokenization and syllable counting"
```

---

### Task 2: Flesch Reading Ease

**Files:** Create `src/bullfighter/flesch.py`; Test `tests/test_flesch.py`.

- [ ] **Step 1: Write failing tests**

```python
import pytest
from bullfighter.flesch import flesch_reading_ease

def test_flesch_simple_sentence():
    # "The cat sat." -> words=3, sentences=1, syllables=3
    # 206.835 - 1.015*(3/1) - 84.6*(3/3) = 119.19
    assert flesch_reading_ease("The cat sat.") == pytest.approx(119.19, abs=0.01)

def test_flesch_empty_is_zero():
    assert flesch_reading_ease("") == 0.0
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_flesch.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `flesch.py`**

```python
from bullfighter.text import words, sentences, count_syllables

def flesch_reading_ease(text: str) -> float:
    w = words(text)
    s = sentences(text)
    if not w or not s:
        return 0.0
    syl = sum(count_syllables(x) for x in w)
    score = 206.835 - 1.015 * (len(w) / len(s)) - 84.6 * (syl / len(w))
    return round(score, 2)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_flesch.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/flesch.py tests/test_flesch.py
git commit -m "feat: Flesch Reading Ease"
```

---

### Task 3: Corpus (schema, load, validate)

**Files:** Create `data/jargon.yaml`, `data/CHANGELOG.md`, `src/bullfighter/corpus.py`; Test `tests/test_corpus.py`.

- [ ] **Step 1: Write seed `data/jargon.yaml`**

```yaml
version: "0.1.0"
entries:
  - term: leverage
    severity: 5
    source: reconstructed
    added: "2026-07-01"
    notes: "Most-cited Bullfighter offender."
  - term: bandwidth
    severity: 5
    source: reconstructed
    added: "2026-07-01"
    notes: "Second most-cited offender."
  - term: synergy
    severity: 4
    source: reconstructed
    added: "2026-07-01"
  - term: robust
    severity: 3
    source: reconstructed
    added: "2026-07-01"
  - term: value-added
    severity: 4
    source: reconstructed
    added: "2026-07-01"
```

- [ ] **Step 2: Write `data/CHANGELOG.md`**

```markdown
# Corpus Changelog

## 0.1.0 — 2026-07-01
- Seed corpus: reconstructed starter set (leverage, bandwidth, synergy, robust,
  value-added) from archived Bullfighter press coverage.
```

- [ ] **Step 3: Write failing tests**

```python
import pytest
from bullfighter.corpus import Corpus, CorpusError

def test_load_default_corpus():
    c = Corpus.load()
    assert c.version == "0.1.0"
    assert "leverage" in c.terms()

def test_severity_case_insensitive():
    assert Corpus.load().severity("LEVERAGE") == 5

def test_reject_bad_severity(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text('version: "0.0.1"\nentries:\n  - {term: x, severity: 9, source: user, added: "2026-07-01"}\n', encoding="utf-8")
    with pytest.raises(CorpusError):
        Corpus.load(p)

def test_reject_duplicates(tmp_path):
    p = tmp_path / "dup.yaml"
    p.write_text('version: "0.0.1"\nentries:\n  - {term: x, severity: 1, source: user, added: "2026-07-01"}\n  - {term: X, severity: 2, source: user, added: "2026-07-01"}\n', encoding="utf-8")
    with pytest.raises(CorpusError):
        Corpus.load(p)
```

- [ ] **Step 4: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_corpus.py -q`
Expected: FAIL — module not found.

- [ ] **Step 5: Implement `corpus.py`**

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

VALID_SOURCES = {"extracted", "reconstructed", "user", "llm-suggested"}
_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "jargon.yaml"

class CorpusError(Exception):
    pass

@dataclass(frozen=True)
class Entry:
    term: str
    severity: int
    source: str
    added: str
    notes: str = ""
    aliases: tuple[str, ...] = ()

class Corpus:
    def __init__(self, version: str, entries: list[Entry]):
        self.version = version
        self._entries = entries
        self._by_term = {e.term.lower(): e for e in entries}

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Corpus":
        p = Path(path) if path else _DEFAULT_PATH
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "version" not in raw or "entries" not in raw:
            raise CorpusError("corpus must have 'version' and 'entries'")
        entries: list[Entry] = []
        seen: set[str] = set()
        for row in raw["entries"]:
            e = Entry(str(row["term"]), int(row["severity"]), str(row["source"]),
                      str(row["added"]), str(row.get("notes", "")),
                      tuple(row.get("aliases", []) or ()))
            if not (1 <= e.severity <= 5):
                raise CorpusError(f"severity out of range for {e.term!r}")
            if e.source not in VALID_SOURCES:
                raise CorpusError(f"bad source for {e.term!r}: {e.source}")
            key = e.term.lower()
            if key in seen:
                raise CorpusError(f"duplicate term: {e.term!r}")
            seen.add(key)
            entries.append(e)
        return cls(str(raw["version"]), entries)

    def terms(self) -> list[str]:
        return [e.term for e in self._entries]

    def entries(self) -> list[Entry]:
        return list(self._entries)

    def severity(self, term: str) -> int | None:
        e = self._by_term.get(term.lower())
        return e.severity if e else None
```

- [ ] **Step 6: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_corpus.py -q`
Expected: PASS (4 passed)

- [ ] **Step 7: Commit**

```bash
git add data/jargon.yaml data/CHANGELOG.md src/bullfighter/corpus.py tests/test_corpus.py
git commit -m "feat: versioned jargon corpus with validation"
```

---

### Task 4: Bull Index (jargon matching)

**Files:** Create `src/bullfighter/bull_index.py`; Test `tests/test_bull_index.py`.

- [ ] **Step 1: Write failing tests**

```python
import pytest
from bullfighter.corpus import Corpus
from bullfighter.bull_index import find_hits, bull_index

C = Corpus.load()

def test_find_hits_terms_and_offsets():
    hits = find_hits("We must leverage synergy now.", C)
    terms = [(h.term, h.severity) for h in hits]
    assert ("leverage", 5) in terms and ("synergy", 4) in terms
    lev = next(h for h in hits if h.term == "leverage")
    assert "We must leverage synergy now."[lev.start:lev.end].lower() == "leverage"

def test_find_hits_word_bounded():
    assert len(find_hits("Leverage the leverages.", C)) == 1

def test_bull_index_zero_when_clean():
    assert bull_index("plain honest words here", C) == 0.0

def test_bull_index_weighted_density():
    # "leverage" sev 5 in 2 words -> 1000 * 5 / 2 = 2500.0
    assert bull_index("leverage now", C) == pytest.approx(2500.0)
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_bull_index.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `bull_index.py`**

```python
from __future__ import annotations
from dataclasses import dataclass
import re
from bullfighter.corpus import Corpus
from bullfighter.text import words

@dataclass(frozen=True)
class Hit:
    term: str
    severity: int
    start: int
    end: int

def find_hits(text: str, corpus: Corpus) -> list[Hit]:
    """Word-bounded, case-insensitive matches of corpus terms."""
    hits: list[Hit] = []
    for entry in corpus.entries():
        pattern = re.compile(r"(?<![A-Za-z])" + re.escape(entry.term) + r"(?![A-Za-z])", re.IGNORECASE)
        for m in pattern.finditer(text):
            hits.append(Hit(entry.term, entry.severity, m.start(), m.end()))
    hits.sort(key=lambda h: h.start)
    return hits

def bull_index(text: str, corpus: Corpus) -> float:
    n = len(words(text))
    if n == 0:
        return 0.0
    total = sum(h.severity for h in find_hits(text, corpus))
    return round(1000.0 * total / n, 2)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_bull_index.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/bull_index.py tests/test_bull_index.py
git commit -m "feat: Bull Index jargon matching and density"
```

---

### Task 5: Bull Composite score

**Files:** Create `src/bullfighter/composite.py`; Test `tests/test_composite.py`.

- [ ] **Step 1: Write failing tests**

```python
import pytest
from bullfighter.composite import bull_composite, FORMULA_VERSION, K_PENALTY

def test_formula_pinned():
    assert FORMULA_VERSION == "bfc-v1" and K_PENALTY == 30.0

def test_clear_text_high():
    # flesch 80 -> 0.8; bull_index 0 -> penalty 0; 1 + 9*0.8 = 8.2
    assert bull_composite(80.0, 0.0) == pytest.approx(8.2)

def test_heavy_jargon_penalized():
    # flesch 80 -> 0.8; bull_index 30 -> penalty 1.0; 1 + 9*0 = 1.0
    assert bull_composite(80.0, 30.0) == pytest.approx(1.0)

def test_clamped():
    assert bull_composite(200.0, 0.0) == pytest.approx(10.0)
    assert bull_composite(-50.0, 0.0) == pytest.approx(1.0)
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_composite.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `composite.py`**

```python
FORMULA_VERSION = "bfc-v1"
K_PENALTY = 30.0

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def bull_composite(flesch: float, bull_index: float) -> float:
    """Combine Flesch (higher=clearer) and Bull Index (higher=worse) into 1..10."""
    flesch_norm = _clamp(flesch / 100.0, 0.0, 1.0)
    jargon_penalty = _clamp(bull_index / K_PENALTY, 0.0, 1.0)
    return round(1.0 + 9.0 * (flesch_norm * (1.0 - jargon_penalty)), 1)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_composite.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/composite.py tests/test_composite.py
git commit -m "feat: Bull Composite score (bfc-v1)"
```

---

### Task 6: Report (the output contract) + top-level API

**Files:** Create `src/bullfighter/report.py`; Modify `src/bullfighter/__init__.py`; Test `tests/test_report.py`.

- [ ] **Step 1: Write failing tests**

```python
from bullfighter.report import score, Report

def test_score_all_fields():
    r = score("We must leverage synergy to win.")
    assert isinstance(r, Report)
    assert r.corpus_version == "0.1.0" and r.formula_version == "bfc-v1"
    assert r.word_count == 6
    assert any(h.term == "leverage" for h in r.hits)
    assert 1.0 <= r.composite <= 10.0

def test_to_dict_json_ready():
    d = score("leverage now").to_dict()
    assert set(d) >= {"composite", "bull_index", "flesch", "word_count", "hits", "corpus_version", "formula_version"}
    assert d["hits"][0]["term"] == "leverage"

def test_public_api():
    import bullfighter
    assert hasattr(bullfighter, "score")
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_report.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `report.py`**

```python
from __future__ import annotations
from dataclasses import dataclass, asdict
from bullfighter.corpus import Corpus
from bullfighter.text import words
from bullfighter.flesch import flesch_reading_ease
from bullfighter.bull_index import find_hits, Hit, bull_index as _bull_index
from bullfighter.composite import bull_composite, FORMULA_VERSION

@dataclass(frozen=True)
class Report:
    composite: float
    bull_index: float
    flesch: float
    word_count: int
    hits: list[Hit]
    corpus_version: str
    formula_version: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["hits"] = [asdict(h) for h in self.hits]
        return d

def score(text: str, corpus: Corpus | None = None) -> Report:
    c = corpus or Corpus.load()
    flesch = flesch_reading_ease(text)
    bi = _bull_index(text, c)
    return Report(
        composite=bull_composite(flesch, bi),
        bull_index=bi,
        flesch=flesch,
        word_count=len(words(text)),
        hits=find_hits(text, c),
        corpus_version=c.version,
        formula_version=FORMULA_VERSION,
    )
```

- [ ] **Step 4: Update `src/bullfighter/__init__.py`**

```python
__version__ = "0.1.0"

from bullfighter.report import score, Report  # noqa: E402

__all__ = ["score", "Report", "__version__"]
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_report.py -q`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add src/bullfighter/report.py src/bullfighter/__init__.py tests/test_report.py
git commit -m "feat: Report contract and top-level score() API"
```

---

### Task 7: Corpus mutation (add/remove/save) — needed by MCP corpus tools

**Files:** Modify `src/bullfighter/corpus.py`; Test append to `tests/test_corpus.py`.

- [ ] **Step 1: Write failing tests (append to `tests/test_corpus.py`)**

```python
def test_add_and_save_roundtrip(tmp_path):
    src = tmp_path / "c.yaml"
    src.write_text('version: "0.1.0"\nentries:\n  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n', encoding="utf-8")
    c = Corpus.load(src)
    c.add("bandwidth", severity=4, source="user", added="2026-07-02", note="test")
    c.save(src)
    assert Corpus.load(src).severity("bandwidth") == 4

def test_add_duplicate_raises():
    c = Corpus.load()
    with pytest.raises(CorpusError):
        c.add("leverage", severity=1, source="user", added="2026-07-02")

def test_remove_term(tmp_path):
    src = tmp_path / "c.yaml"
    src.write_text('version: "0.1.0"\nentries:\n  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n  - {term: synergy, severity: 4, source: reconstructed, added: "2026-07-01"}\n', encoding="utf-8")
    c = Corpus.load(src)
    c.remove("synergy")
    assert c.severity("synergy") is None and c.severity("leverage") == 5
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_corpus.py -q`
Expected: FAIL — `Corpus` has no attribute `add`.

- [ ] **Step 3: Add mutation methods to `corpus.py` (after `severity`)**

```python
    def add(self, term, severity, source, added, note="", aliases=()):
        if self.severity(term) is not None:
            raise CorpusError(f"term already exists: {term!r}")
        if not (1 <= int(severity) <= 5):
            raise CorpusError("severity must be 1..5")
        if source not in VALID_SOURCES:
            raise CorpusError(f"bad source: {source}")
        e = Entry(str(term), int(severity), str(source), str(added), str(note), tuple(aliases))
        self._entries.append(e)
        self._by_term[e.term.lower()] = e

    def remove(self, term):
        key = term.lower()
        if key not in self._by_term:
            raise CorpusError(f"no such term: {term!r}")
        del self._by_term[key]
        self._entries = [e for e in self._entries if e.term.lower() != key]

    def save(self, path):
        rows = []
        for e in self._entries:
            row = {"term": e.term, "severity": e.severity, "source": e.source, "added": e.added}
            if e.notes:
                row["notes"] = e.notes
            if e.aliases:
                row["aliases"] = list(e.aliases)
            rows.append(row)
        Path(path).write_text(
            yaml.safe_dump({"version": self.version, "entries": rows}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_corpus.py -q`
Expected: PASS (all corpus tests)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/corpus.py tests/test_corpus.py
git commit -m "feat: corpus mutation (add/remove/save)"
```

---

### Task 8: Document parsing (.txt / .docx)

**Files:** Create `src/bullfighter/parse.py`; Test `tests/test_parse.py`.

- [ ] **Step 1: Write failing tests**

```python
import pytest
from docx import Document
from bullfighter.parse import read_text

def test_read_txt(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello leverage", encoding="utf-8")
    assert read_text(p) == "hello leverage"

def test_read_docx(tmp_path):
    p = tmp_path / "a.docx"
    doc = Document(); doc.add_paragraph("We must leverage synergy."); doc.save(p)
    assert "leverage synergy" in read_text(p)

def test_unsupported_raises(tmp_path):
    p = tmp_path / "a.pdf"; p.write_bytes(b"%PDF")
    with pytest.raises(ValueError):
        read_text(p)
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_parse.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `parse.py`**

```python
from __future__ import annotations
from pathlib import Path

def read_text(path: Path | str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".txt":
        return p.read_text(encoding="utf-8")
    if ext == ".docx":
        from docx import Document
        return "\n".join(para.text for para in Document(str(p)).paragraphs)
    raise ValueError(f"unsupported file type: {ext} (v1 supports .txt, .docx)")
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_parse.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/parse.py tests/test_parse.py
git commit -m "feat: read .txt and .docx documents"
```

---

### Task 9: MCP server (the headline deliverable)

**Files:** Create `src/bullfighter/mcp_server.py`; Test `tests/test_mcp_server.py`; Modify `README.md`.

**Design note:** each tool's logic lives in a plain helper function (`_score_text`,
etc.); the `@mcp.tool()`-decorated wrapper just calls it. Tests exercise the
decorated tools directly (FastMCP's decorator returns the function unchanged), so
they're deterministic and robust across SDK versions. No network, no subprocess.

- [ ] **Step 1: Confirm the FastMCP import for the installed SDK**

Run: `.venv/Scripts/python -c "from mcp.server.fastmcp import FastMCP; print('ok')"`
Expected: `ok`.
If it errors (newer SDK renamed the class), run
`.venv/Scripts/python -c "import mcp.server, pkgutil; print([m.name for m in pkgutil.iter_modules(mcp.server.__path__)])"`
and use the module that provides the server class; adjust the import in Step 3
accordingly. Record the working import in `docs/recovery-notes.md` is not needed —
just use it consistently below.

- [ ] **Step 2: Write failing tests**

```python
from bullfighter import mcp_server as S

def test_score_text_tool_returns_report_dict():
    d = S.score_text("We must leverage synergy to win.")
    assert d["formula_version"] == "bfc-v1"
    assert d["corpus_version"] == "0.1.0"
    assert any(h["term"] == "leverage" for h in d["hits"])
    assert 1.0 <= d["composite"] <= 10.0

def test_find_jargon_tool_lists_hits():
    d = S.find_jargon("leverage bandwidth")
    assert d["count"] == 2
    assert {h["term"] for h in d["hits"]} == {"leverage", "bandwidth"}

def test_corpus_list_tool():
    d = S.corpus_list()
    assert "leverage" in [e["term"] for e in d["entries"]]
    assert d["version"] == "0.1.0"

def test_corpus_add_tool_writes(tmp_path, monkeypatch):
    src = tmp_path / "c.yaml"
    src.write_text('version: "0.1.0"\nentries:\n  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n', encoding="utf-8")
    monkeypatch.setattr(S, "CORPUS_PATH", src)
    out = S.corpus_add("bandwidth", severity=4, source="user", note="x")
    assert out["ok"] is True
    from bullfighter.corpus import Corpus
    assert Corpus.load(src).severity("bandwidth") == 4

def test_server_object_is_fastmcp():
    from mcp.server.fastmcp import FastMCP
    assert isinstance(S.mcp, FastMCP)
```

- [ ] **Step 3: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_mcp_server.py -q`
Expected: FAIL — module not found.

- [ ] **Step 4: Implement `mcp_server.py`**

```python
from __future__ import annotations
import datetime as _dt
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from bullfighter.report import score as _score
from bullfighter.corpus import Corpus, _DEFAULT_PATH

mcp = FastMCP("bullfighter")

# Overridable in tests; defaults to the packaged corpus.
CORPUS_PATH: Path = _DEFAULT_PATH


@mcp.tool()
def score_text(text: str) -> dict:
    """Score text for jargon and readability. Returns Bull Composite (1-10, 10=clearest),
    Bull Index, Flesch Reading Ease, word count, jargon hits with offsets, and versions."""
    return _score(text, Corpus.load(CORPUS_PATH)).to_dict()


@mcp.tool()
def find_jargon(text: str) -> dict:
    """List jargon terms found in the text, with severity and character offsets."""
    r = _score(text, Corpus.load(CORPUS_PATH))
    return {
        "count": len(r.hits),
        "hits": [{"term": h.term, "severity": h.severity, "start": h.start, "end": h.end} for h in r.hits],
        "corpus_version": r.corpus_version,
    }


@mcp.tool()
def corpus_list() -> dict:
    """List all jargon terms in the corpus with severity and provenance."""
    c = Corpus.load(CORPUS_PATH)
    return {
        "version": c.version,
        "entries": [{"term": e.term, "severity": e.severity, "source": e.source} for e in c.entries()],
    }


@mcp.tool()
def corpus_add(term: str, severity: int, source: str = "user", note: str = "") -> dict:
    """Add a jargon term to the corpus (persisted). severity 1-5; source defaults to 'user'."""
    c = Corpus.load(CORPUS_PATH)
    c.add(term, severity=severity, source=source, added=_dt.date.today().isoformat(), note=note)
    c.save(CORPUS_PATH)
    return {"ok": True, "term": term, "severity": severity, "source": source}


def run() -> None:
    """Console entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    run()
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_mcp_server.py -q`
Expected: PASS (5 passed)

- [ ] **Step 6: Smoke-test the server starts over stdio**

Run: `.venv/Scripts/python -c "from bullfighter.mcp_server import mcp; import anyio; print('tools:', anyio.run(lambda: mcp.list_tools()))"`
Expected: prints a list including `score_text`, `find_jargon`, `corpus_list`, `corpus_add`.
(If `list_tools()` signature differs in the installed SDK, skip this optional smoke check — the pytest suite already proves the tools work.)

- [ ] **Step 7: Add MCP client config to `README.md`** (append)

```markdown
## Use as an MCP server

After `pip install -e .`, register the server with any MCP client.

**Claude Desktop / Claude Code** (`claude_desktop_config.json` or `claude mcp add`):

```json
{
  "mcpServers": {
    "bullfighter": {
      "command": "bullfighter-mcp"
    }
  }
}
```

Tools exposed: `score_text`, `find_jargon`, `corpus_list`, `corpus_add`.
The client's own model handles explanation and rewriting, grounded on the
deterministic scores these tools return.
```

- [ ] **Step 8: Commit**

```bash
git add src/bullfighter/mcp_server.py tests/test_mcp_server.py README.md
git commit -m "feat: MCP server exposing engine + corpus as tools"
```

---

### Task 10: Lean CLI (local testing + golden values)

**Files:** Create `src/bullfighter/cli.py`; Test `tests/test_cli.py`.

- [ ] **Step 1: Write failing tests**

```python
import json
from click.testing import CliRunner
from bullfighter.cli import main

def test_score_text_json():
    res = CliRunner().invoke(main, ["score", "--text", "leverage now", "--json"])
    assert res.exit_code == 0
    assert json.loads(res.output)["hits"][0]["term"] == "leverage"

def test_score_text_human():
    res = CliRunner().invoke(main, ["score", "--text", "We must leverage synergy."])
    assert res.exit_code == 0 and "Bull Composite" in res.output and "leverage" in res.output

def test_corpus_list():
    res = CliRunner().invoke(main, ["corpus", "list"])
    assert res.exit_code == 0 and "leverage" in res.output
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_cli.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `cli.py`**

```python
from __future__ import annotations
import json as _json
import sys
import click
from bullfighter.report import score as _score
from bullfighter.parse import read_text
from bullfighter.corpus import Corpus

def _get_text(path, text):
    if text is not None:
        return text
    if path:
        return read_text(path)
    return sys.stdin.read()

def _render(r):
    lines = [
        f"Bull Composite: {r.composite}/10   (10 = clearest)",
        f"Flesch Reading Ease: {r.flesch}",
        f"Bull Index: {r.bull_index}   words: {r.word_count}",
        f"corpus {r.corpus_version} / formula {r.formula_version}",
    ]
    lines += (["Jargon:"] + [f"  - {h.term} (severity {h.severity}) @ {h.start}" for h in r.hits]) if r.hits else ["No jargon found."]
    return "\n".join(lines)

@click.group()
def main():
    """Bullfighter: detect jargon, score clarity."""

@main.command()
@click.argument("path", required=False)
@click.option("--text", default=None)
@click.option("--json", "as_json", is_flag=True)
def score(path, text, as_json):
    """Score a document or --text."""
    r = _score(_get_text(path, text))
    click.echo(_json.dumps(r.to_dict()) if as_json else _render(r))

@main.group()
def corpus():
    """Inspect the jargon corpus."""

@corpus.command("list")
def corpus_list():
    for e in Corpus.load().entries():
        click.echo(f"{e.term}\tsev {e.severity}\t{e.source}")
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_cli.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/cli.py tests/test_cli.py
git commit -m "feat: lean CLI for local scoring and corpus inspection"
```

---

### Task 11: Golden-file score tests (drift guard)

**Files:** Create `tests/golden/samples/jargon_heavy.txt`, `tests/golden/samples/clean.txt`, `tests/golden/test_golden.py`.

- [ ] **Step 1: Write sample fixtures**

`tests/golden/samples/jargon_heavy.txt`:
```
We must leverage our synergy and bandwidth to deliver robust value-added outcomes.
```
`tests/golden/samples/clean.txt`:
```
We will use our skills and time to do good work that helps our customers.
```

- [ ] **Step 2: Write the golden test (scaffold — literals filled in Step 4)**

```python
from pathlib import Path
import pytest
from bullfighter.report import score

SAMPLES = Path(__file__).parent / "samples"

# Filled with real literals in Step 4. DO NOT ship self-references.
EXPECTED = {
    "jargon_heavy": {"composite": None, "bull_index": None},
    "clean": {"composite": None, "bull_index": None},
}

@pytest.mark.parametrize("name", ["jargon_heavy", "clean"])
def test_scores_stable(name):
    r = score((SAMPLES / f"{name}.txt").read_text(encoding="utf-8"))
    assert r.composite == EXPECTED[name]["composite"]
    assert r.bull_index == EXPECTED[name]["bull_index"]
```

- [ ] **Step 3: Compute the real values**

Run: `.venv/Scripts/bullfighter score tests/golden/samples/jargon_heavy.txt --json`
Run: `.venv/Scripts/bullfighter score tests/golden/samples/clean.txt --json`
Record `composite` and `bull_index` for each.

- [ ] **Step 4: Replace the `None`s with the recorded literals, then run**

Run: `.venv/Scripts/pytest tests/golden/test_golden.py -q`
Expected: PASS (2 passed) with hard-coded numbers (e.g. `{"composite": 1.0, "bull_index": 1272.73}`).

- [ ] **Step 5: Commit**

```bash
git add tests/golden
git commit -m "test: golden-file score fixtures to guard against drift"
```

---

### Task 12: Installer recovery tool (investigative, seeds corpus)

**Files:** Create `tools/extract_installer.py`, `docs/recovery-notes.md`.

Investigative reverse-engineering, not TDD — DLL internals are unknown until
opened. Follow the procedure; record findings; enrich the corpus. Graceful
fallback is expected and acceptable.

- [ ] **Step 1: Unpack the Wise installer payload**

Source `Bullfighter.exe` is in the user's Downloads (a Wise Installation Wizard
package). Try, in order, logging what worked in `docs/recovery-notes.md`:
1. `7z l "C:/Users/William/Downloads/Bullfighter.exe"` then `7z x ... -oextracted/`.
2. If that fails, `binwalk -e` or a Python `pefile` resource dump.
3. Identify the add-in artifact (`.dll`, `.dot`/`.dotm` template, or data file).

- [ ] **Step 2: Locate the embedded word list**

`strings -n 4 <artifact>` and look for business-word clusters (leverage, synergy,
paradigm, bandwidth, robust, incentivize, …); or dump PE resources via `pefile`.
Record the raw recovered list verbatim in `docs/recovery-notes.md`.

- [ ] **Step 3: Look for formula constants**

Search for the Flesch coefficients (206.835 / 1.015 / 84.6) or severity tables to
recover the real Bull Index/Composite weighting. If found, document them — they
may justify a future `bfc-v2`.

- [ ] **Step 4: Write `tools/extract_installer.py`**

A re-runnable script automating whatever extraction path worked: takes the
installer path, extracts, greps candidate words, writes `data/recovered_terms.yaml`
(entries tagged `source: extracted`) for human review. If nothing is recoverable,
print a clear message and exit 0 — the seed corpus stands.

- [ ] **Step 5: Merge recovered terms (human-reviewed)**

For each accepted term, `bullfighter corpus add` isn't in the lean CLI, so use the
MCP `corpus_add` tool or hand-edit `data/jargon.yaml`; bump `version` to `0.2.0`
and add a `CHANGELOG.md` entry citing the extraction source. Re-run the suite;
update golden literals in the same commit if scores shift.

- [ ] **Step 6: Commit**

```bash
git add tools/extract_installer.py docs/recovery-notes.md data/ tests/golden
git commit -m "feat: installer recovery tool + recovered corpus terms"
```

---

### Task 13: CI + lint + full green run

**Files:** Create `.github/workflows/ci.yml`.

- [ ] **Step 1: Write CI workflow**

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -e ".[dev]"
      - run: ruff check src tests
      - run: pytest -q
```

- [ ] **Step 2: Run lint + tests locally**

Run: `.venv/Scripts/ruff check src tests && .venv/Scripts/pytest -q`
Expected: ruff clean; all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: lint and test on push/PR"
```

---

## Self-Review

**Spec coverage:**
- Layer 1 engine → Tasks 1,2,4,5,6 ✅
- Layer 2 corpus (versioned, updatable, provenance, changelog) → Tasks 3,7 ✅
- **MCP server (now primary surface)** → Task 9 (tools: score_text, find_jargon, corpus_list, corpus_add) ✅
- Layer 3 CLI (lean, local) → Task 10 ✅
- `.txt`/`.docx` parsing → Task 8 ✅
- Fidelity/extraction (best-effort + fallback) → Task 12 ✅
- `corpus_version` on every Report/tool result → Tasks 6, 9 ✅
- Golden tests / drift guard → Task 11 ✅
- LLM layer → **client-side via MCP** (no self-hosted layer in v1); optional future Plan 2.
- MCP client config documented → Task 9 Step 7 ✅
- `.pptx`, web app, GUI → non-goals, excluded ✅

**Placeholder scan:** Task 11 ships explicit `None` sentinels the engineer replaces
with computed literals in Step 4 (flagged, not hidden). Task 12 is investigative by
design with a documented fallback. Task 9 Step 1 handles SDK import drift explicitly.
No hidden placeholders.

**Type consistency:** `Corpus.load/severity/entries/add/remove/save`,
`_DEFAULT_PATH`, `find_hits→Hit(term,severity,start,end)`, `score()→Report`,
`Report.to_dict()`, `bull_composite(flesch, bull_index)`, `FORMULA_VERSION`,
`K_PENALTY`, and MCP tools `score_text/find_jargon/corpus_list/corpus_add` — names
consistent across Tasks 3–13. ✅

---

## Notes for later plans (not this plan)

- **Optional self-hosted LLM layer:** `explain.py` / `rewrite.py` for non-MCP
  callers (Anthropic default per the `claude-api` skill); rewrite re-scores via
  `score()` and surfaces only if `composite` improves. Not needed while the MCP
  client's own model does this.
- **`corpus suggest` MCP tool:** propose candidate bullwords from a document into a
  human-approved queue (`source: llm-suggested`), never auto-committed.
- **`/bullfighter` Claude Code skill:** thin wrapper over the MCP server.
- **`.pptx` parsing** and richer offset highlighting.
