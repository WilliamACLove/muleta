from muleta.text import words, sentences, count_syllables


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
