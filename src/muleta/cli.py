from __future__ import annotations

import json as _json
import sys

import click

from muleta.corpus import Corpus
from muleta.parse import read_text
from muleta.report import score as _score


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
    if r.hits:
        lines.append("Jargon:")
        lines += [f"  - {h.term} (severity {h.severity}) @ {h.start}" for h in r.hits]
    else:
        lines.append("No jargon found.")
    return "\n".join(lines)


@click.group()
def main():
    """Muleta: detect jargon, score clarity."""


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
