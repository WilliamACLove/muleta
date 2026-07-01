import json

from click.testing import CliRunner

from muleta.cli import main


def test_score_text_json():
    res = CliRunner().invoke(main, ["score", "--text", "leverage now", "--json"])
    assert res.exit_code == 0
    assert json.loads(res.output)["hits"][0]["term"] == "leverage"


def test_score_text_human():
    res = CliRunner().invoke(main, ["score", "--text", "We must leverage synergy."])
    assert res.exit_code == 0
    assert "Bull Composite Index" in res.output and "leverage" in res.output


def test_corpus_list():
    res = CliRunner().invoke(main, ["corpus", "list"])
    assert res.exit_code == 0 and "leverage" in res.output
