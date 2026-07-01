from muleta.text import words, sentences, count_syllables


def flesch_reading_ease(text: str) -> float:
    w = words(text)
    s = sentences(text)
    if not w or not s:
        return 0.0
    syl = sum(count_syllables(x) for x in w)
    score = 206.835 - 1.015 * (len(w) / len(s)) - 84.6 * (syl / len(w))
    return round(score, 2)
