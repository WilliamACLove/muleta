from muleta.pending import PendingQueue


def test_propose_and_count(tmp_path):
    p = tmp_path / "pending.yaml"
    q = PendingQueue.load(p)
    q.propose("circle back", example="let's circle back", reason="filler")
    q.propose("circle back")  # proposed again -> count 2
    q.save()
    reloaded = PendingQueue.load(p)
    e = reloaded.get("circle back")
    assert e is not None and e.count == 2
    assert e.example == "let's circle back"


def test_remove(tmp_path):
    p = tmp_path / "pending.yaml"
    q = PendingQueue.load(p)
    q.propose("synergize")
    q.remove("synergize")
    q.save()
    assert PendingQueue.load(p).get("synergize") is None
