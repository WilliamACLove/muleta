from __future__ import annotations

from dataclasses import asdict, dataclass

from muleta.bull_index import Hit, bull_scores
from muleta.composite import FORMULA_VERSION, bull_composite
from muleta.corpus import Corpus
from muleta.flesch import adjusted_flesch, flesch_reading_ease


@dataclass(frozen=True)
class Report:
    composite: float  # Bull Composite Index (BCI), 0..10, 10 = clearest
    bull_index: float  # BI, 0..10
    bull_index_raw: float  # BIr, 0..100 (the vendor's displayed jargon score)
    flesch: float  # raw Flesch Reading Ease
    flesch_adjusted: float  # AF, 0..10 (educated-readership adjusted)
    word_count: int
    weight_factor: int  # F, the length-based bull weight factor
    hits: list[Hit]
    corpus_version: str
    formula_version: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["hits"] = [asdict(h) for h in self.hits]
        return d


def score(text: str, corpus: Corpus | None = None) -> Report:
    c = corpus or Corpus.load()
    bir, bi, f, hits = bull_scores(text, c)
    raw_flesch = flesch_reading_ease(text)
    af = adjusted_flesch(raw_flesch)
    from muleta.text import words

    return Report(
        composite=bull_composite(bi, af),
        bull_index=bi,
        bull_index_raw=bir,
        flesch=raw_flesch,
        flesch_adjusted=af,
        word_count=len(words(text)),
        weight_factor=f,
        hits=hits,
        corpus_version=c.version,
        formula_version=FORMULA_VERSION,
    )
