from muleta import usage
from muleta.report import score


def test_record_and_aggregate(monkeypatch, tmp_path):
    path = tmp_path / "usage.jsonl"
    monkeypatch.setenv("MULETA_USAGE_PATH", str(path))
    monkeypatch.delenv("MULETA_NO_USAGE", raising=False)
    usage.record(score("We must leverage synergy."))
    usage.record(score("We must leverage our bandwidth."))
    stats = usage.aggregate()
    assert stats["documents"] == 2
    terms = {t["term"]: t for t in stats["terms"]}
    assert terms["leverage"]["occurrences"] == 2
    assert terms["leverage"]["documents"] == 2


def test_disabled_via_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MULETA_USAGE_PATH", str(tmp_path / "u.jsonl"))
    monkeypatch.setenv("MULETA_NO_USAGE", "1")
    assert usage.enabled() is False
    assert usage.record(score("leverage")) is False
    assert usage.aggregate()["documents"] == 0
