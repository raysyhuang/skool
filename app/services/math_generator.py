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
    else:
        # Grade 2 level: two-digit add/subtract, simple times tables, easy missing number
        modes = ["addition_easy", "subtraction_easy", "multiplication_easy", "missing_number_easy"]
        weights = [30, 30, 25, 15]

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
}
