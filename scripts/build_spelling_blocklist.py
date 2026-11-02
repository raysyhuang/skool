"""Rebuild app/services/spelling_blocklist.txt.

The sight-word spelling question makes wrong answers by randomly editing a
word, and some edits land on real words ("then" -> "than", "on" -> "no").
This lists every real word any single edit can produce, so the generator can
skip them. Needs a word list (macOS ships /usr/share/dict/words).

    python scripts/build_spelling_blocklist.py [/path/to/words]
"""
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.english_generator import (  # noqa: E402
    _SIGHT_WORDS_EASY, _SIGHT_WORDS_MEDIUM,
)

VOWELS, CONSONANTS = "aeiou", "bcdfghjklmnpqrstvwxyz"


def edits(word: str) -> set[str]:
    """Everything _make_misspellings can return for `word`."""
    out = {word + s for s in ("e", "s", "ee", "ss", word[-1])}
    letters = list(word)
    if len(letters) < 2:
        out |= set(string.ascii_lowercase)
        return out - {word}
    for i in range(len(letters) - 1):
        w = letters[:]
        w[i], w[i + 1] = w[i + 1], w[i]
        out.add("".join(w))
    for i, ch in enumerate(letters):
        for c in VOWELS if ch in VOWELS else CONSONANTS:
            out.add("".join(letters[:i] + [c] + letters[i + 1:]))
    if len(letters) >= 3:
        for i in range(1, len(letters)):
            out.add("".join(letters[:i] + [letters[i]] + letters[i:]))
            out.add("".join(letters[:i] + letters[i + 1:]))
    return out - {word}


def main() -> None:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/dict/words")
    real = {w.strip().lower() for w in source.read_text().split()}
    candidates = set().union(*(edits(w) for w in _SIGHT_WORDS_EASY + _SIGHT_WORDS_MEDIUM))
    blocked = sorted(candidates & real)
    out = Path(__file__).resolve().parent.parent / "app/services/spelling_blocklist.txt"
    out.write_text("\n".join(blocked) + "\n")
    print(f"{len(blocked)} words -> {out}")


if __name__ == "__main__":
    main()
