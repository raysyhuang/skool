import json
import random


# Emoji sets for counting mode
_COUNTING_EMOJIS = ["🍎", "🍊", "🍋", "🍉", "🍇", "🍓", "🌟", "🚗", "🐟", "🎈"]


def generate_math_questions(age: int, count: int = 5) -> list[dict]:
    """Generate age-appropriate math questions.

    Returns list of dicts with: mode, expression, prompt_text, prompt_image,
    correct_answer, options, prompt_data (JSON string).
    """
    if age <= 5:
        modes = ["counting", "addition_simple", "subtraction_simple"]
        weights = [40, 35, 25]
    elif age <= 7:
        # Grade 2 level: two-digit add/subtract, simple times tables, easy missing number
        modes = ["addition_easy", "subtraction_easy", "multiplication_easy", "missing_number_easy"]
        weights = [30, 30, 25, 15]
    else:
        # Grade 3-4 level: full times tables, division, fractions, 3-digit arithmetic
        modes = [
            "addition_medium", "subtraction_medium", "multiplication_medium",
            "division_basic", "fractions_compare", "missing_number_medium",
        ]
        weights = [15, 15, 25, 20, 15, 10]

    questions = []
    for _ in range(count):
        mode = random.choices(modes, weights=weights, k=1)[0]
        q = _GENERATORS[mode]()
        questions.append(q)
    return questions


def _gen_counting() -> dict:
    n = random.randint(1, 10)
    emoji = random.choice(_COUNTING_EMOJIS)
    visual = emoji * n
    correct = str(n)
    options = _make_number_distractors(n, 1, 10)
    return _build(
        mode="counting",
        expression=visual,
        prompt_text="How many?",
        prompt_image=visual,
        correct_answer=correct,
        options=options,
    )


def _gen_addition_simple() -> dict:
    a = random.randint(1, 9)
    b = random.randint(1, 10 - a)
    ans = a + b
    expression = f"{a} + {b} = ?"
    options = _make_number_distractors(ans, 1, 10)
    return _build(
        mode="addition_simple",
        expression=expression,
        prompt_text=f"What is {a} + {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_subtraction_simple() -> dict:
    a = random.randint(2, 10)
    b = random.randint(1, a)
    ans = a - b
    expression = f"{a} - {b} = ?"
    options = _make_number_distractors(ans, 0, 10)
    return _build(
        mode="subtraction_simple",
        expression=expression,
        prompt_text=f"What is {a} - {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_addition_easy() -> dict:
    """Grade 2: two-digit + single/two-digit, sums up to 100."""
    a = random.randint(10, 60)
    b = random.randint(1, 40)
    ans = a + b
    expression = f"{a} + {b} = ?"
    options = _make_number_distractors(ans, max(0, ans - 10), ans + 10)
    return _build(
        mode="addition_easy",
        expression=expression,
        prompt_text=f"What is {a} + {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_subtraction_easy() -> dict:
    """Grade 2: two-digit - single/two-digit, result >= 0."""
    a = random.randint(20, 80)
    b = random.randint(1, min(a, 30))
    ans = a - b
    expression = f"{a} - {b} = ?"
    options = _make_number_distractors(ans, max(0, ans - 10), ans + 10)
    return _build(
        mode="subtraction_easy",
        expression=expression,
        prompt_text=f"What is {a} - {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_multiplication_easy() -> dict:
    """Grade 2: times tables up to 5 x 5."""
    a = random.randint(2, 5)
    b = random.randint(2, 5)
    ans = a * b
    expression = f"{a} x {b} = ?"
    options = _make_number_distractors(ans, max(1, ans - 5), ans + 5)
    return _build(
        mode="multiplication_easy",
        expression=expression,
        prompt_text=f"What is {a} x {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_missing_number_easy() -> dict:
    """Grade 2: simple missing number with + or - only, numbers up to 20."""
    op = random.choice(["+", "-"])
    if op == "+":
        ans = random.randint(1, 15)
        b = random.randint(1, 10)
        result = ans + b
        expression = f"___ + {b} = {result}"
        prompt_text = f"___ + {b} = {result}"
    else:
        ans = random.randint(5, 20)
        b = random.randint(1, min(ans - 1, 10))
        result = ans - b
        expression = f"___ - {b} = {result}"
        prompt_text = f"___ - {b} = {result}"
    options = _make_number_distractors(ans, max(1, ans - 5), ans + 5)
    return _build(
        mode="missing_number_easy",
        expression=expression,
        prompt_text=prompt_text,
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


# ── Grade 3-4 (age 8+) ──

def _gen_addition_medium() -> dict:
    """Grade 3: 3-digit addition, sums up to 1000."""
    a = random.randint(100, 700)
    b = random.randint(50, min(999 - a, 300))
    ans = a + b
    expression = f"{a} + {b} = ?"
    options = _make_number_distractors(ans, max(0, ans - 20), ans + 20)
    return _build(
        mode="addition_medium",
        expression=expression,
        prompt_text=f"What is {a} + {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_subtraction_medium() -> dict:
    """Grade 3: 3-digit subtraction, result >= 0."""
    a = random.randint(200, 900)
    b = random.randint(50, min(a, 300))
    ans = a - b
    expression = f"{a} - {b} = ?"
    options = _make_number_distractors(ans, max(0, ans - 20), ans + 20)
    return _build(
        mode="subtraction_medium",
        expression=expression,
        prompt_text=f"What is {a} - {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_multiplication_medium() -> dict:
    """Grade 3-4: full times tables up to 12 x 12."""
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    ans = a * b
    expression = f"{a} x {b} = ?"
    options = _make_number_distractors(ans, max(1, ans - 8), ans + 8)
    return _build(
        mode="multiplication_medium",
        expression=expression,
        prompt_text=f"What is {a} x {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_division_basic() -> dict:
    """Grade 3: basic division with no remainder."""
    divisor = random.randint(2, 10)
    quotient = random.randint(2, 12)
    dividend = divisor * quotient
    ans = quotient
    expression = f"{dividend} ÷ {divisor} = ?"
    options = _make_number_distractors(ans, max(1, ans - 3), ans + 3)
    return _build(
        mode="division_basic",
        expression=expression,
        prompt_text=f"What is {dividend} ÷ {divisor}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


# Fraction pool for comparisons and identification
_FRACTION_POOL = [
    ("1/2", 0.5), ("1/3", 1 / 3), ("1/4", 0.25), ("2/3", 2 / 3),
    ("3/4", 0.75), ("1/5", 0.2), ("2/5", 0.4), ("3/5", 0.6),
    ("1/8", 0.125), ("3/8", 0.375), ("1/10", 0.1),
]


def _gen_fractions_compare() -> dict:
    """Grade 3: compare two fractions — which is bigger?"""
    pair = random.sample(_FRACTION_POOL, 2)
    name1, val1 = pair[0]
    name2, val2 = pair[1]
    # Ensure they're not equal
    while abs(val1 - val2) < 0.001:
        pair = random.sample(_FRACTION_POOL, 2)
        name1, val1 = pair[0]
        name2, val2 = pair[1]

    if val1 > val2:
        correct = name1
    else:
        correct = name2

    # Third option: pick another fraction
    others = [n for n, v in _FRACTION_POOL if n != name1 and n != name2]
    third = random.choice(others) if others else "1/6"

    options = [name1, name2, third]
    random.shuffle(options)

    return _build(
        mode="fractions_compare",
        expression=f"{name1}  or  {name2} ?",
        prompt_text="Which fraction is BIGGER?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_missing_number_medium() -> dict:
    """Grade 3-4: missing number with +, -, or x, larger numbers."""
    op = random.choice(["+", "-", "x"])
    if op == "+":
        ans = random.randint(20, 200)
        b = random.randint(10, 100)
        result = ans + b
        expression = f"___ + {b} = {result}"
        prompt_text = f"___ + {b} = {result}"
    elif op == "-":
        ans = random.randint(50, 300)
        b = random.randint(10, min(ans - 1, 100))
        result = ans - b
        expression = f"___ - {b} = {result}"
        prompt_text = f"___ - {b} = {result}"
    else:
        ans = random.randint(2, 12)
        b = random.randint(2, 12)
        result = ans * b
        expression = f"___ x {b} = {result}"
        prompt_text = f"___ x {b} = {result}"
    options = _make_number_distractors(ans, max(1, ans - 5), ans + 5)
    return _build(
        mode="missing_number_medium",
        expression=expression,
        prompt_text=prompt_text,
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _make_number_distractors(correct: int, low: int, high: int) -> list[str]:
    """Generate 2 plausible wrong answers near the correct one, return shuffled list of 3."""
    distractors = set()
    nearby = list(range(max(low, correct - 3), min(high, correct + 3) + 1))
    nearby = [n for n in nearby if n != correct]
    random.shuffle(nearby)
    for n in nearby:
        distractors.add(n)
        if len(distractors) >= 2:
            break
    # Fill remaining if needed
    while len(distractors) < 2:
        d = correct + random.choice([-1, 1, -2, 2, 3])
        if d != correct and d >= 0:
            distractors.add(d)
    options = [str(correct)] + [str(d) for d in list(distractors)[:2]]
    random.shuffle(options)
    return options


def _build(mode: str, expression: str, prompt_text: str, prompt_image: str | None,
           correct_answer: str, options: list[str]) -> dict:
    prompt_data = json.dumps({
        "mode": mode,
        "expression": expression,
        "prompt_text": prompt_text,
        "prompt_image": prompt_image,
        "correct_answer": correct_answer,
    })
    return {
        "mode": mode,
        "expression": expression,
        "prompt_text": prompt_text,
        "prompt_image": prompt_image,
        "correct_answer": correct_answer,
        "options": options,
        "prompt_data": prompt_data,
    }


_GENERATORS = {
    "counting": _gen_counting,
    "addition_simple": _gen_addition_simple,
    "subtraction_simple": _gen_subtraction_simple,
    "addition_easy": _gen_addition_easy,
    "subtraction_easy": _gen_subtraction_easy,
    "multiplication_easy": _gen_multiplication_easy,
    "missing_number_easy": _gen_missing_number_easy,
    "addition_medium": _gen_addition_medium,
    "subtraction_medium": _gen_subtraction_medium,
    "multiplication_medium": _gen_multiplication_medium,
    "division_basic": _gen_division_basic,
    "fractions_compare": _gen_fractions_compare,
    "missing_number_medium": _gen_missing_number_medium,
}
