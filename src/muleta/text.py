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
