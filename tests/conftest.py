import pytest


@pytest.fixture(autouse=True)
def _isolate_usage(tmp_path, monkeypatch):
    """Point usage logging at a per-test temp file so tests never touch ~/.muleta."""
    monkeypatch.setenv("MULETA_USAGE_PATH", str(tmp_path / "usage.jsonl"))
