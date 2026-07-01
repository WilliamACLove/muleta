# Bullfighter Phase 1 — Recovery + Core Engine + Corpus + CLI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the deterministic Bullfighter engine — jargon detection + Flesch + Bull Composite (1–10) — with a versioned, updatable corpus and a CLI, all without any LLM.

**Architecture:** A pure-Python core engine turns text into a structured `Report` (Bull Index, Flesch Reading Ease, Bull Composite, jargon hits with offsets, corpus version). The jargon corpus is a versioned YAML dataset with provenance and a changelog. A CLI wraps the engine for humans and scripts, including `corpus` management verbs. A separate investigative tool attempts to recover the original ~350-word dictionary and formula constants from the installer, seeding the corpus (graceful fallback to a documented reconstruction).

**Tech Stack:** Python 3.11+, `pytest`, `pyyaml`, `python-docx`, `click` (CLI), `ruff` (lint). Packaged with `pyproject.toml` (setuptools).

---

## File Structure

```
bullfighter/
├─ pyproject.toml                 packaging, deps, console_scripts entry point
├─ README.md                      what/why/how, links to methodology
├─ src/bullfighter/
│   ├─ __init__.py                version, public API re-exports
│   ├─ text.py                    tokenize words, split sentences, count syllables
│   ├─ flesch.py                  Flesch Reading Ease
│   ├─ corpus.py                  load / validate / version / mutate the dictionary
│   ├─ bull_index.py              jargon matching + severity → Bull Index
│   ├─ composite.py               Bull Composite (1–10), formula versioned
│   ├─ report.py                  Report dataclass (the single output contract)
│   ├─ parse.py                   read .txt / .docx into plain text
│   └─ cli.py                     `bullfighter score|dejargon|corpus`
├─ data/
│   ├─ jargon.yaml                the corpus (seed + recovered)
│   └─ CHANGELOG.md               corpus change history
├─ tools/
│   └─ extract_installer.py       investigative recovery from Bullfighter.exe
└─ tests/
    ├─ test_text.py
    ├─ test_flesch.py
    ├─ test_corpus.py
    ├─ test_bull_index.py
    ├─ test_composite.py
    ├─ test_report.py
    ├─ test_parse.py
    ├─ test_cli.py
    └─ golden/
        ├─ samples/…              fixture documents
        └─ test_golden.py         locked expected scores
```

---

## Scoring Definitions (authoritative — tasks below implement exactly these)

**Flesch Reading Ease:** `206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words)`.

**Bull Index:** weighted jargon density.
`bull_index = 1000 × (Σ severity of hits) / word_count` (0 when no words). Higher = more jargon = worse.

**Bull Composite (1–10, 10 = clearest):** transparent, versioned "Bullfighter-compatible v1" formula.
- `flesch_norm = clamp(flesch / 100, 0, 1)`
- `jargon_penalty = clamp(bull_index / K_PENALTY, 0, 1)` with `K_PENALTY = 30.0`
- `composite01 = flesch_norm × (1 − jargon_penalty)`
- `composite = round(1 + 9 × composite01, 1)` → in [1.0, 10.0]

`FORMULA_VERSION = "bfc-v1"`. Constants live in `composite.py` and are pinned by golden tests. If Task 11 recovers real constants, that becomes `bfc-v2` in a later change — never a silent edit.

---

### Task 0: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/bullfighter/__init__.py`
- Create: `README.md`
- Create: `tests/__init__.py` (empty)

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "bullfighter"
version = "0.1.0"
description = "Revival of Deloitte's Bullfighter: jargon detection + readability scoring."
requires-python = ">=3.11"
dependencies = ["pyyaml>=6", "python-docx>=1.1", "click>=8.1"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.5"]

[project.scripts]
bullfighter = "bullfighter.cli:main"

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
# Bullfighter

A revival of Deloitte Consulting's discontinued Bullfighter (2003–2005): detect
business jargon and score writing clarity. Deterministic engine (Bull Index +
Flesch Reading Ease + Bull Composite 1–10) with a versioned, updatable jargon
corpus and a CLI. See `docs/` for methodology and provenance.
```

- [ ] **Step 4: Create venv and install dev deps**

Run: `python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"`
Expected: installs bullfighter in editable mode, exit 0.

- [ ] **Step 5: Verify pytest runs (no tests yet)**

Run: `.venv/Scripts/pytest -q`
Expected: "no tests ran" (exit 5) — confirms discovery works.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/bullfighter/__init__.py README.md tests/__init__.py
git commit -m "chore: scaffold bullfighter package"
```

---

### Task 1: Text utilities (words, sentences, syllables)

**Files:**
- Create: `src/bullfighter/text.py`
- Test: `tests/test_text.py`

- [ ] **Step 1: Write failing tests**

```python
from bullfighter.text import words, sentences, count_syllables

def test_words_basic():
    assert words("The cat sat.") == ["The", "cat", "sat"]

def test_words_ignores_punctuation_and_numbers_are_dropped():
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
    """Heuristic syllable count: vowel groups, minus common silent trailing 'e'.

    Not linguistically perfect; good enough for readability scoring and locked
    by tests so it cannot drift silently.
    """
    w = word.lower()
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return 0
    groups = _VOWEL_GROUP_RE.findall(w)
    count = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ie", "ee", "ye")) and count > 1:
        count -= 1
    return max(count, 1)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_text.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add src/bullfighter/text.py tests/test_text.py
git commit -m "feat: text tokenization and syllable counting"
```

---

### Task 2: Flesch Reading Ease

**Files:**
- Create: `src/bullfighter/flesch.py`
- Test: `tests/test_flesch.py`

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
    total_syllables = sum(count_syllables(x) for x in w)
    score = (
        206.835
        - 1.015 * (len(w) / len(s))
        - 84.6 * (total_syllables / len(w))
    )
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

**Files:**
- Create: `data/jargon.yaml`
- Create: `data/CHANGELOG.md`
- Create: `src/bullfighter/corpus.py`
- Test: `tests/test_corpus.py`

- [ ] **Step 1: Write seed `data/jargon.yaml`** (reconstructed starter set from press coverage; extraction later enriches it)

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

def test_load_default_corpus_has_version_and_entries():
    c = Corpus.load()
    assert c.version == "0.1.0"
    assert "leverage" in c.terms()

def test_severity_lookup_is_case_insensitive():
    c = Corpus.load()
    assert c.severity("LEVERAGE") == 5

def test_validate_rejects_bad_severity(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        'version: "0.0.1"\n'
        'entries:\n'
        '  - {term: x, severity: 9, source: user, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorpusError):
        Corpus.load(bad)

def test_validate_rejects_duplicate_terms(tmp_path):
    dup = tmp_path / "dup.yaml"
    dup.write_text(
        'version: "0.0.1"\n'
        'entries:\n'
        '  - {term: x, severity: 1, source: user, added: "2026-07-01"}\n'
        '  - {term: X, severity: 2, source: user, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorpusError):
        Corpus.load(dup)
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
            e = Entry(
                term=str(row["term"]),
                severity=int(row["severity"]),
                source=str(row["source"]),
                added=str(row["added"]),
                notes=str(row.get("notes", "")),
                aliases=tuple(row.get("aliases", []) or ()),
            )
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

**Files:**
- Create: `src/bullfighter/bull_index.py`
- Test: `tests/test_bull_index.py`

- [ ] **Step 1: Write failing tests**

```python
import pytest
from bullfighter.corpus import Corpus
from bullfighter.bull_index import find_hits, bull_index

C = Corpus.load()

def test_find_hits_returns_term_and_offsets():
    hits = find_hits("We must leverage synergy now.", C)
    terms = [(h.term, h.severity) for h in hits]
    assert ("leverage", 5) in terms
    assert ("synergy", 4) in terms
    # offsets point at the matched substring
    lev = next(h for h in hits if h.term == "leverage")
    assert "We must leverage synergy now."[lev.start:lev.end].lower() == "leverage"

def test_find_hits_is_case_insensitive_and_word_bounded():
    # "leverages" should NOT match "leverage" (word-bounded)
    assert find_hits("Leverage the leverages.", C) and \
        all(h.term == "leverage" for h in find_hits("Leverage the leverages.", C))
    assert len(find_hits("Leverage the leverages.", C)) == 1

def test_bull_index_zero_when_no_jargon():
    assert bull_index("plain honest words here", C) == 0.0

def test_bull_index_weighted_density():
    # "leverage" (sev 5) in a 2-word doc -> 1000 * 5 / 2 = 2500.0
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
    """Word-bounded, case-insensitive matches of corpus terms in text."""
    hits: list[Hit] = []
    for entry in corpus.entries():
        pattern = re.compile(
            r"(?<![A-Za-z])" + re.escape(entry.term) + r"(?![A-Za-z])",
            re.IGNORECASE,
        )
        for m in pattern.finditer(text):
            hits.append(Hit(entry.term, entry.severity, m.start(), m.end()))
    hits.sort(key=lambda h: h.start)
    return hits

def bull_index(text: str, corpus: Corpus) -> float:
    n = len(words(text))
    if n == 0:
        return 0.0
    total_severity = sum(h.severity for h in find_hits(text, corpus))
    return round(1000.0 * total_severity / n, 2)
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

**Files:**
- Create: `src/bullfighter/composite.py`
- Test: `tests/test_composite.py`

- [ ] **Step 1: Write failing tests**

```python
import pytest
from bullfighter.composite import bull_composite, FORMULA_VERSION, K_PENALTY

def test_formula_version_is_pinned():
    assert FORMULA_VERSION == "bfc-v1"
    assert K_PENALTY == 30.0

def test_composite_clear_text_scores_high():
    # flesch=80 -> norm 0.8; bull_index=0 -> penalty 0; composite = 1 + 9*0.8 = 8.2
    assert bull_composite(flesch=80.0, bull_index=0.0) == pytest.approx(8.2)

def test_composite_heavy_jargon_penalized():
    # flesch=80 -> 0.8; bull_index=30 -> penalty 1.0; composite = 1 + 9*0 = 1.0
    assert bull_composite(flesch=80.0, bull_index=30.0) == pytest.approx(1.0)

def test_composite_clamped_to_range():
    assert bull_composite(flesch=200.0, bull_index=0.0) == pytest.approx(10.0)
    assert bull_composite(flesch=-50.0, bull_index=0.0) == pytest.approx(1.0)
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
    composite01 = flesch_norm * (1.0 - jargon_penalty)
    return round(1.0 + 9.0 * composite01, 1)
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

### Task 6: Report (the output contract)

**Files:**
- Create: `src/bullfighter/report.py`
- Modify: `src/bullfighter/__init__.py` (re-export `score`)
- Test: `tests/test_report.py`

- [ ] **Step 1: Write failing tests**

```python
from bullfighter.report import score, Report

def test_score_returns_report_with_all_fields():
    r = score("We must leverage synergy to win.")
    assert isinstance(r, Report)
    assert r.corpus_version == "0.1.0"
    assert r.formula_version == "bfc-v1"
    assert r.word_count == 6
    assert any(h.term == "leverage" for h in r.hits)
    assert 1.0 <= r.composite <= 10.0

def test_report_to_dict_is_json_ready():
    d = score("leverage now").to_dict()
    assert set(d) >= {
        "composite", "bull_index", "flesch", "word_count",
        "hits", "corpus_version", "formula_version",
    }
    assert isinstance(d["hits"], list)
    assert d["hits"][0]["term"] == "leverage"

def test_public_api_exports_score():
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

### Task 7: Document parsing (.txt / .docx)

**Files:**
- Create: `src/bullfighter/parse.py`
- Test: `tests/test_parse.py`

- [ ] **Step 1: Write failing tests**

```python
import pytest
from docx import Document
from bullfighter.parse import read_text

def test_read_plain_text(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello leverage", encoding="utf-8")
    assert read_text(p) == "hello leverage"

def test_read_docx(tmp_path):
    p = tmp_path / "a.docx"
    doc = Document()
    doc.add_paragraph("We must leverage synergy.")
    doc.save(p)
    assert "leverage synergy" in read_text(p)

def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(b"%PDF")
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
        doc = Document(str(p))
        return "\n".join(para.text for para in doc.paragraphs)
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

### Task 8: CLI — `score` and `dejargon` (report only)

**Files:**
- Create: `src/bullfighter/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
import json
from click.testing import CliRunner
from bullfighter.cli import main

def test_score_text_json():
    res = CliRunner().invoke(main, ["score", "--text", "leverage now", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["hits"][0]["term"] == "leverage"
    assert data["formula_version"] == "bfc-v1"

def test_score_text_human():
    res = CliRunner().invoke(main, ["score", "--text", "We must leverage synergy."])
    assert res.exit_code == 0
    assert "Bull Composite" in res.output
    assert "leverage" in res.output

def test_score_file(tmp_path):
    p = tmp_path / "d.txt"
    p.write_text("leverage synergy", encoding="utf-8")
    res = CliRunner().invoke(main, ["score", str(p), "--json"])
    assert res.exit_code == 0
    assert json.loads(res.output)["word_count"] == 2
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_cli.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `cli.py`** (score + dejargon placeholder that reports)

```python
from __future__ import annotations
import json as _json
import sys
import click
from bullfighter.report import score as _score
from bullfighter.parse import read_text

def _get_text(path: str | None, text: str | None) -> str:
    if text is not None:
        return text
    if path:
        return read_text(path)
    return sys.stdin.read()

def _render_human(r) -> str:
    lines = [
        f"Bull Composite: {r.composite}/10   (10 = clearest)",
        f"Flesch Reading Ease: {r.flesch}",
        f"Bull Index: {r.bull_index}   words: {r.word_count}",
        f"corpus {r.corpus_version} / formula {r.formula_version}",
    ]
    if r.hits:
        lines.append("Jargon:")
        for h in r.hits:
            lines.append(f"  - {h.term} (severity {h.severity}) @ {h.start}")
    else:
        lines.append("No jargon found.")
    return "\n".join(lines)

@click.group()
def main() -> None:
    """Bullfighter: detect jargon, score clarity."""

@main.command()
@click.argument("path", required=False)
@click.option("--text", default=None, help="Score this string instead of a file.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def score(path: str | None, text: str | None, as_json: bool) -> None:
    """Score a document or --text."""
    r = _score(_get_text(path, text))
    click.echo(_json.dumps(r.to_dict()) if as_json else _render_human(r))
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_cli.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Verify installed entry point**

Run: `.venv/Scripts/bullfighter score --text "We must leverage synergy."`
Expected: human-readable report naming "leverage" and "synergy".

- [ ] **Step 6: Commit**

```bash
git add src/bullfighter/cli.py tests/test_cli.py
git commit -m "feat: CLI score command"
```

---

### Task 9: CLI — `corpus` management verbs

**Files:**
- Modify: `src/bullfighter/corpus.py` (add mutation + save)
- Modify: `src/bullfighter/cli.py` (add `corpus` group)
- Test: `tests/test_corpus.py` (add mutation tests), `tests/test_cli.py` (add corpus CLI tests)

- [ ] **Step 1: Write failing tests (mutation in `corpus.py`)** — append to `tests/test_corpus.py`

```python
def test_add_and_save_roundtrip(tmp_path):
    from bullfighter.corpus import Corpus
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "0.1.0"\nentries:\n'
        '  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    c = Corpus.load(src)
    c.add("bandwidth", severity=4, source="user", added="2026-07-02", note="test")
    c.save(src)
    reloaded = Corpus.load(src)
    assert reloaded.severity("bandwidth") == 4

def test_add_duplicate_raises(tmp_path):
    from bullfighter.corpus import Corpus, CorpusError
    import pytest
    c = Corpus.load()
    with pytest.raises(CorpusError):
        c.add("leverage", severity=1, source="user", added="2026-07-02")

def test_remove_term(tmp_path):
    from bullfighter.corpus import Corpus
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "0.1.0"\nentries:\n'
        '  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n'
        '  - {term: synergy, severity: 4, source: reconstructed, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    c = Corpus.load(src)
    c.remove("synergy")
    assert c.severity("synergy") is None
    assert c.severity("leverage") == 5
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_corpus.py -q`
Expected: FAIL — `Corpus` has no attribute `add`.

- [ ] **Step 3: Add mutation methods to `corpus.py`** (insert after `severity`)

```python
    def add(self, term, severity, source, added, note="", aliases=()):
        if self.severity(term) is not None:
            raise CorpusError(f"term already exists: {term!r}")
        if not (1 <= int(severity) <= 5):
            raise CorpusError("severity must be 1..5")
        if source not in VALID_SOURCES:
            raise CorpusError(f"bad source: {source}")
        e = Entry(str(term), int(severity), str(source), str(added),
                  str(note), tuple(aliases))
        self._entries.append(e)
        self._by_term[e.term.lower()] = e

    def remove(self, term):
        key = term.lower()
        if key not in self._by_term:
            raise CorpusError(f"no such term: {term!r}")
        del self._by_term[key]
        self._entries = [e for e in self._entries if e.term.lower() != key]

    def save(self, path):
        from pathlib import Path
        rows = []
        for e in self._entries:
            row = {"term": e.term, "severity": e.severity,
                   "source": e.source, "added": e.added}
            if e.notes:
                row["notes"] = e.notes
            if e.aliases:
                row["aliases"] = list(e.aliases)
            rows.append(row)
        payload = {"version": self.version, "entries": rows}
        Path(path).write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_corpus.py -q`
Expected: PASS (all corpus tests)

- [ ] **Step 5: Write failing CLI tests** — append to `tests/test_cli.py`

```python
def test_corpus_list_shows_seed_terms():
    from bullfighter.cli import main
    from click.testing import CliRunner
    res = CliRunner().invoke(main, ["corpus", "list"])
    assert res.exit_code == 0
    assert "leverage" in res.output

def test_corpus_add_writes_entry(tmp_path):
    from bullfighter.cli import main
    from click.testing import CliRunner
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "0.1.0"\nentries:\n'
        '  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    res = CliRunner().invoke(main, [
        "corpus", "add", "bandwidth", "--severity", "4",
        "--source", "user", "--corpus", str(src),
    ])
    assert res.exit_code == 0
    from bullfighter.corpus import Corpus
    assert Corpus.load(src).severity("bandwidth") == 4
```

- [ ] **Step 6: Run to verify fail**

Run: `.venv/Scripts/pytest tests/test_cli.py -q`
Expected: FAIL — no `corpus` command.

- [ ] **Step 7: Add `corpus` group to `cli.py`** (append at end of file)

```python
import datetime as _dt
from bullfighter.corpus import Corpus

@main.group()
def corpus() -> None:
    """Inspect and update the jargon corpus."""

@corpus.command("list")
@click.option("--corpus", "corpus_path", default=None)
def corpus_list(corpus_path: str | None) -> None:
    c = Corpus.load(corpus_path) if corpus_path else Corpus.load()
    for e in c.entries():
        click.echo(f"{e.term}\tsev {e.severity}\t{e.source}")

@corpus.command("add")
@click.argument("term")
@click.option("--severity", type=int, required=True)
@click.option("--source", default="user")
@click.option("--note", default="")
@click.option("--corpus", "corpus_path", default=None)
def corpus_add(term, severity, source, note, corpus_path) -> None:
    c = Corpus.load(corpus_path) if corpus_path else Corpus.load()
    today = _dt.date.today().isoformat()
    c.add(term, severity=severity, source=source, added=today, note=note)
    target = corpus_path or str(
        __import__("bullfighter.corpus", fromlist=["_DEFAULT_PATH"])._DEFAULT_PATH
    )
    c.save(target)
    click.echo(f"added {term!r} (severity {severity}, source {source})")

@corpus.command("remove")
@click.argument("term")
@click.option("--corpus", "corpus_path", default=None)
def corpus_remove(term, corpus_path) -> None:
    c = Corpus.load(corpus_path) if corpus_path else Corpus.load()
    c.remove(term)
    target = corpus_path or str(
        __import__("bullfighter.corpus", fromlist=["_DEFAULT_PATH"])._DEFAULT_PATH
    )
    c.save(target)
    click.echo(f"removed {term!r}")
```

- [ ] **Step 8: Run to verify pass**

Run: `.venv/Scripts/pytest tests/test_cli.py -q`
Expected: PASS (all CLI tests)

- [ ] **Step 9: Commit**

```bash
git add src/bullfighter/corpus.py src/bullfighter/cli.py tests/test_corpus.py tests/test_cli.py
git commit -m "feat: corpus management (list/add/remove) via API and CLI"
```

---

### Task 10: Golden-file score tests (drift guard)

**Files:**
- Create: `tests/golden/samples/jargon_heavy.txt`
- Create: `tests/golden/samples/clean.txt`
- Create: `tests/golden/test_golden.py`

- [ ] **Step 1: Write sample fixtures**

`tests/golden/samples/jargon_heavy.txt`:
```
We must leverage our synergy and bandwidth to deliver robust value-added outcomes.
```
`tests/golden/samples/clean.txt`:
```
We will use our skills and time to do good work that helps our customers.
```

- [ ] **Step 2: Write golden test that first prints, then locks values**

```python
from pathlib import Path
import pytest
from bullfighter.report import score

SAMPLES = Path(__file__).parent / "samples"

@pytest.mark.parametrize("name", ["jargon_heavy", "clean"])
def test_scores_are_stable(name):
    text = (SAMPLES / f"{name}.txt").read_text(encoding="utf-8")
    r = score(text)
    # Lock the current deterministic output. If the engine or corpus changes
    # intentionally, update these numbers in the same commit (never silently).
    expected = {
        "jargon_heavy": {"composite": r.composite, "bull_index": r.bull_index},
        "clean": {"composite": r.composite, "bull_index": r.bull_index},
    }[name]
    assert r.composite == expected["composite"]
    assert r.bull_index == expected["bull_index"]
```

> Implementation note for the engineer: run the sample through the CLI once
> (`bullfighter score tests/golden/samples/jargon_heavy.txt --json`), read the
> real `composite` and `bull_index`, and **replace the `r.composite` /
> `r.bull_index` self-references above with the literal numbers**. The self-
> reference is a scaffold so the test file is valid before you fill it in; the
> committed version MUST contain hard-coded literals, e.g.
> `{"composite": 1.0, "bull_index": 1272.73}`.

- [ ] **Step 3: Compute real values**

Run: `.venv/Scripts/bullfighter score tests/golden/samples/jargon_heavy.txt --json`
Run: `.venv/Scripts/bullfighter score tests/golden/samples/clean.txt --json`
Record both `composite` and `bull_index`.

- [ ] **Step 4: Replace self-references with literals and run**

Run: `.venv/Scripts/pytest tests/golden/test_golden.py -q`
Expected: PASS (2 passed) with hard-coded literals.

- [ ] **Step 5: Commit**

```bash
git add tests/golden
git commit -m "test: golden-file score fixtures to guard against drift"
```

---

### Task 11: Installer recovery tool (investigative, seeds corpus)

**Files:**
- Create: `tools/extract_installer.py`
- Create: `docs/recovery-notes.md`

This task is **investigative reverse-engineering**, not TDD — the DLL internals
are unknown until opened. Follow the procedure; record findings; enrich the
corpus with anything recovered. Graceful fallback is expected and acceptable.

- [ ] **Step 1: Unpack the Wise installer payload**

The source `Bullfighter.exe` (in the user's Downloads) is a Wise Installation
Wizard package. Attempt extraction, in order, and log which worked in
`docs/recovery-notes.md`:
1. `7z l Bullfighter.exe` then `7z x Bullfighter.exe -oextracted/` (7-Zip often
   lists Wise payloads).
2. If 7-Zip fails, try the Python `unwise`/`wcx` approaches or `binwalk -e`.
3. Identify the installed add-in artifact (a `.dll`, `.dot`/`.dot m` Word
   template, or a data file) among the extracted files.

- [ ] **Step 2: Locate the embedded word list**

In the extracted artifact, search for the dictionary:
- `strings -n 4 <artifact> | less` and look for clusters of business words
  (leverage, synergy, paradigm, bandwidth, robust, incentivize, …).
- If the list is in a resource section, use `pefile` (Python) to enumerate
  resources and dump candidates.
Record the raw recovered list verbatim in `docs/recovery-notes.md`.

- [ ] **Step 3: Look for formula constants**

Search the artifact for the Bull Index / Composite computation (numeric
constants near the Flesch coefficients 206.835 / 1.015 / 84.6, or severity
tables). If found, document them; they may justify a future `bfc-v2`.

- [ ] **Step 4: Write `tools/extract_installer.py`**

A small, re-runnable script that automates whatever extraction path worked in
Step 1–2: takes the installer path, extracts, greps candidate words, and writes
a `data/recovered_terms.yaml` draft (all entries tagged `source: extracted`) for
human review. If nothing is recoverable, the script prints a clear message and
exits 0 — the seed corpus stands.

- [ ] **Step 5: Merge recovered terms into the corpus (human-reviewed)**

For each recovered term a human accepts, use `bullfighter corpus add <term>
--severity N --source user` (or hand-edit `data/jargon.yaml`), then bump
`data/jargon.yaml` `version` to `0.2.0` and add a `CHANGELOG.md` entry noting
the extraction source. Re-run the full test suite; update golden literals in the
same commit if scores shift.

- [ ] **Step 6: Commit**

```bash
git add tools/extract_installer.py docs/recovery-notes.md data/ tests/golden
git commit -m "feat: installer recovery tool + recovered corpus terms"
```

---

### Task 12: CI + lint + full green run

**Files:**
- Create: `.github/workflows/ci.yml`

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
- Layer 2 corpus (versioned, updatable, provenance, changelog) → Tasks 3,9 ✅
- Layer 3 CLI (score + corpus verbs; .txt/.docx) → Tasks 7,8,9 ✅
- Fidelity/extraction (best-effort + fallback) → Task 11 ✅
- `corpus_version` on every Report → Task 6 ✅
- Golden tests / drift guard → Task 10 ✅
- Layers 4 (LLM), 5 (MCP), 6 (skill) → **deferred to Plans 2–4** (noted at top).
- `.pptx`, web app, GUI → non-goals, correctly excluded. ✅

**Placeholder scan:** Task 10 intentionally ships a scaffold self-reference and
tells the engineer to replace it with literals — flagged explicitly, not a
hidden TODO. Task 11 is investigative by nature with a documented procedure and
fallback. No hidden placeholders elsewhere.

**Type consistency:** `Corpus.load/severity/entries/add/remove/save`,
`find_hits→Hit(term,severity,start,end)`, `score()→Report`, `Report.to_dict()`,
`bull_composite(flesch, bull_index)`, `FORMULA_VERSION`, `K_PENALTY` — names
consistent across Tasks 3–10. ✅

---

## Notes for Plans 2–4 (not this plan)

- **Plan 2 (LLM layer):** `llm/client.py` (Anthropic default, per `claude-api`
  skill), `explain.py`, `rewrite.py` (re-scores its rewrite via `score()` and
  surfaces only if `composite` improves), `context_scan.py`, and
  `bullfighter corpus suggest` feeding a human-approved review queue.
- **Plan 3 (MCP):** thin server exposing `bull_score(text)` and `de_jargon(text)`
  over the same `score()` / LLM functions.
- **Plan 4 (skill):** `/bullfighter` Claude Code skill wrapping the CLI/MCP.
