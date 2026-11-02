"""Every generated question must have exactly one defensible answer."""
from unittest import mock

import pytest

from app.models.character import Character
from app.services import english_generator, logic_generator, math_generator
from app.services.question_generator import generate_character_options, generate_options

ROUNDS = 300


def _generated(generators: dict, *args):
    for mode, gen in generators.items():
        for _ in range(ROUNDS):
            yield mode, gen(*args)


@pytest.mark.parametrize("generators,args", [
    (logic_generator._GENERATORS, ()),
    (math_generator._GENERATORS, ()),
    (english_generator._GENERATORS, (9,)),
])
def test_answer_is_offered_once_among_distinct_options(generators, args):
    for mode, q in _generated(generators, *args):
        assert len(set(q["options"])) == len(q["options"]), (mode, q["options"])
        assert q["options"].count(q["correct_answer"]) == 1, (mode, q)


def test_pen_analogy_no_longer_offers_draw():
    pen = [a for a in logic_generator._WORD_ANALOGIES if "pen" in a[0]]
    assert pen and all("draw" not in opts for _, _, opts in pen)


def test_letter_sound_distractors_never_share_the_answers_sound():
    for _ in range(ROUNDS):
        q = english_generator._gen_letter_sound(4)
        right = set(q["correct_answer"].split()[0].split("/"))
        for opt in q["options"]:
            if opt != q["correct_answer"]:
                assert not right & set(opt.split()[0].split("/")), q["options"]


def test_misspellings_are_never_real_words():
    words = english_generator._SIGHT_WORDS_EASY + english_generator._SIGHT_WORDS_MEDIUM
    for word in words:
        for _ in range(30):
            wrong = english_generator._make_misspellings(word, 2)
            assert len(wrong) == 2 and word not in wrong
            assert not set(wrong) & english_generator._REAL_WORDS, (word, wrong)


def test_soft_is_not_a_wrong_answer_for_opposite_of_loud():
    with mock.patch.object(english_generator, "_ANTONYMS", [("loud", "quiet"), ("hard", "soft"), ("hot", "cold")]):
        for _ in range(ROUNDS):
            q = english_generator._gen_antonym_match(9)
            if "'loud'" in q["prompt_text"]:
                assert "soft" not in q["options"]


def test_fraction_answer_is_the_biggest_option():
    values = dict(math_generator._FRACTION_POOL) | {"0": 0}
    for _ in range(ROUNDS):
        q = math_generator._gen_fractions_compare()
        assert values[q["correct_answer"]] == max(values[o] for o in q["options"])


@pytest.mark.parametrize("number,to,expected", [(250, 100, "300"), (350, 100, "400"), (125, 10, "130")])
def test_rounding_halves_round_up(number, to, expected):
    with mock.patch.object(math_generator.random, "choice", return_value=to), \
         mock.patch.object(math_generator.random, "randint", return_value=number):
        assert math_generator._gen_rounding()["correct_answer"] == expected


def test_chinese_distractors_never_share_meaning_or_pinyin(db):
    rows = [("口", "kǒu", "mouth"), ("嘴巴", "zuǐ ba", "mouth"), ("心", "xīn", "heart"),
            ("新", "xīn", "new"), ("画", "huà", "draw/paint"), ("画画", "huà huà", "draw"),
            ("大", "dà", "big"), ("小", "xiǎo", "small"), ("水", "shuǐ", "water")]
    chars = {}
    for char, pinyin, meaning in rows:
        chars[char] = Character(character=char, pinyin=pinyin, meaning=meaning,
                                difficulty=1, tags="t", target_users="all")
        db.add(chars[char])
    db.commit()

    for _ in range(100):
        assert "嘴巴" not in generate_character_options(db, chars["口"])
        assert "新" not in generate_character_options(db, chars["心"])
        assert "draw/paint" not in generate_options(db, chars["画画"])
