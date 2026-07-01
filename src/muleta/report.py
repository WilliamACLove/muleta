from __future__ import annotations

from dataclasses import asdict, dataclass

from muleta.bull_index import Hit, bull_index as _bull_index, find_hits
from muleta.composite import FORMULA_VERSION, bull_composite
from muleta.corpus import Corpus
from muleta.flesch import flesch_reading_ease
from muleta.text import words


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
