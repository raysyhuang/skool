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
        modes = ["addition_multi", "subtraction_multi", "multiplication", "division", "missing_number"]
        weights = [20, 20, 25, 20, 15]

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


def _gen_addition_multi() -> dict:
    a = random.randint(10, 500)
    b = random.randint(10, 500)
    ans = a + b
    expression = f"{a} + {b} = ?"
    options = _make_number_distractors(ans, max(0, ans - 20), ans + 20)
    return _build(
        mode="addition_multi",
        expression=expression,
        prompt_text=f"What is {a} + {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_subtraction_multi() -> dict:
    a = random.randint(50, 999)
    b = random.randint(10, a)
    ans = a - b
    expression = f"{a} - {b} = ?"
    options = _make_number_distractors(ans, max(0, ans - 20), ans + 20)
    return _build(
        mode="subtraction_multi",
        expression=expression,
        prompt_text=f"What is {a} - {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_multiplication() -> dict:
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    ans = a * b
    expression = f"{a} × {b} = ?"
    options = _make_number_distractors(ans, max(1, ans - 10), ans + 10)
    return _build(
        mode="multiplication",
        expression=expression,
        prompt_text=f"What is {a} × {b}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_division() -> dict:
    divisor = random.randint(2, 12)
    quotient = random.randint(2, 12)
    dividend = divisor * quotient
    expression = f"{dividend} ÷ {divisor} = ?"
    options = _make_number_distractors(quotient, max(1, quotient - 5), quotient + 5)
    return _build(
        mode="division",
        expression=expression,
        prompt_text=f"What is {dividend} ÷ {divisor}?",
        prompt_image=None,
        correct_answer=str(quotient),
        options=options,
    )


def _gen_missing_number() -> dict:
    op = random.choice(["+", "-", "×"])
    if op == "+":
        ans = random.randint(1, 50)
        b = random.randint(1, 50)
        result = ans + b
        expression = f"___ + {b} = {result}"
        prompt_text = f"___ + {b} = {result}"
    elif op == "-":
        ans = random.randint(1, 50)
        b = random.randint(1, ans)
        result = ans - b
        expression = f"___ - {b} = {result}"
        prompt_text = f"___ - {b} = {result}"
    else:
        ans = random.randint(2, 12)
        b = random.randint(2, 12)
        result = ans * b
        expression = f"___ × {b} = {result}"
        prompt_text = f"___ × {b} = {result}"
    options = _make_number_distractors(ans, max(1, ans - 5), ans + 5)
    return _build(
        mode="missing_number",
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
    "addition_multi": _gen_addition_multi,
    "subtraction_multi": _gen_subtraction_multi,
    "multiplication": _gen_multiplication,
    "division": _gen_division,
    "missing_number": _gen_missing_number,
}
