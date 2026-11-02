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
            "place_value", "rounding", "fraction_of_amount",
            "equivalent_fractions", "factors_multiples",
        ]
        weights = [10, 10, 16, 13, 10, 7, 8, 8, 6, 6, 6]

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
        hint=f"Hold up {a} fingers, then {b} more. Count them all!",
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
        hint=f"Hold up {a} fingers. Put {b} down. How many are left?",
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
        hint=f"Add the tens first: {a // 10 * 10} + {b // 10 * 10}. Then the ones: {a % 10} + {b % 10}.",
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
        hint=_take_away_in_steps(a, b),
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
        hint=f"{a} groups of {b}: " + " + ".join([str(b)] * a),
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
        hint=_think_backwards(op, b, result),
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
        hint=(f"Hundreds: {a // 100 * 100} + {b // 100 * 100}. "
              f"Tens: {a // 10 % 10 * 10} + {b // 10 % 10 * 10}. "
              f"Ones: {a % 10} + {b % 10}. Now add the three parts!"),
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
        hint=_take_away_in_steps(a, b),
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
        hint=f"Skip-count by {b}, {a} times: {b}, {2 * b}, …" if a > 2 else f"Double {b}.",
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
        hint=f"How many {divisor}s make {dividend}? Skip-count: {divisor}, {2 * divisor}, {3 * divisor}, …",
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

    # Third option: another fraction smaller than both, so the question's
    # answer stays the biggest of everything on screen
    others = [n for n, v in _FRACTION_POOL if v < min(val1, val2) - 0.001]
    third = random.choice(others) if others else "0"

    options = [name1, name2, third]
    random.shuffle(options)

    return _build(
        mode="fractions_compare",
        hint=_same_bottom_hint(name1, name2),
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
        hint=_think_backwards(op, b, result),
        expression=expression,
        prompt_text=prompt_text,
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


# ── Additional Grade 3-4 modes (added to widen taxonomy topic coverage) ──

_PLACE_NAMES = [(1, "ones"), (10, "tens"), (100, "hundreds"), (1000, "thousands")]


def _gen_place_value() -> dict:
    """What is the digit actually worth? Place value, not digit-naming."""
    # Distinct digits: "what is the 1 worth" has two right answers in 1419.
    digits = random.sample(range(1, 10), 4)
    number = int("".join(str(d) for d in digits))
    slot = random.randint(0, 3)                 # 0 = ones ... 3 = thousands
    place, place_name = _PLACE_NAMES[slot]
    digit = digits[3 - slot]
    ans = digit * place

    # Distractors are the same digit in the wrong place — the actual mistake.
    wrong = [digit * pl for pl, _ in _PLACE_NAMES if pl != place]
    random.shuffle(wrong)
    options = [str(ans)] + [str(w) for w in wrong[:2]]
    random.shuffle(options)

    return _build(
        mode="place_value",
        hint=f"From the right: ones, tens, hundreds, thousands. Which place is the {digit} in?",
        expression=str(number),
        prompt_text=f"In {number}, what is the {digit} worth?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_rounding() -> dict:
    """Round to the nearest 10 or 100."""
    to = random.choice([10, 100])
    number = random.randint(120, 989)
    while number % to == 0:                     # an exact multiple teaches nothing
        number = random.randint(120, 989)
    ans = (number + to // 2) // to * to         # round half up; round() goes to even

    down, up = (number // to) * to, ((number // to) + 1) * to
    other = up if ans == down else down
    options = [str(ans), str(other), str(number)]
    random.shuffle(options)

    return _build(
        mode="rounding",
        hint=(f"Look at the {'ones' if to == 10 else 'tens'} digit: {number // (to // 10) % 10}. "
              "5 or more rounds up; less than 5 rounds down."),
        expression=f"{number} \u2192 nearest {to}",
        prompt_text=f"Round {number} to the nearest {to}",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_fraction_of_amount() -> dict:
    """What is 3/4 of 12? — fractions as operators on a quantity."""
    denominator = random.choice([2, 3, 4, 5, 6])
    numerator = random.randint(1, denominator - 1)
    whole = denominator * random.randint(2, 6)
    ans = whole * numerator // denominator

    unit = whole // denominator                 # the classic slip: forgetting the numerator
    wrong = {unit, whole - ans, ans + unit}
    wrong.discard(ans)
    wrong = [w for w in wrong if w > 0][:2]
    while len(wrong) < 2:
        candidate = ans + random.choice([-2, -1, 1, 2, 3])
        if candidate > 0 and candidate != ans and candidate not in wrong:
            wrong.append(candidate)

    options = [str(ans)] + [str(w) for w in wrong]
    random.shuffle(options)

    return _build(
        mode="fraction_of_amount",
        hint=f"Split {whole} into {denominator} equal groups, then take {numerator} of them.",
        expression=f"{numerator}/{denominator} of {whole}",
        prompt_text=f"What is {numerator}/{denominator} of {whole}?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _gen_equivalent_fractions() -> dict:
    """Which fraction is equal to this one?"""
    base_n, base_d = random.choice([(1, 2), (1, 3), (1, 4), (2, 3), (3, 4), (2, 5)])
    factor = random.randint(2, 4)
    correct = f"{base_n * factor}/{base_d * factor}"

    wrong = set()
    while len(wrong) < 2:
        n = base_n * factor + random.choice([-1, 1, 2])
        d = base_d * factor + random.choice([-1, 1, 2])
        if n < 1 or d < 2 or n >= d and base_n < base_d:
            continue
        if n * base_d == d * base_n:            # accidentally equivalent
            continue
        wrong.add(f"{n}/{d}")

    options = [correct] + list(wrong)
    random.shuffle(options)

    return _build(
        mode="equivalent_fractions",
        hint="Multiply the top AND the bottom by the same number — try 2, 3 or 4.",
        expression=f"{base_n}/{base_d} = ?",
        prompt_text=f"Which fraction is the SAME as {base_n}/{base_d}?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_factors_multiples() -> dict:
    """Factor or multiple — the pair children most often confuse."""
    if random.random() < 0.5:
        number = random.choice([12, 18, 20, 24, 30, 36])
        factors = [f for f in range(2, number) if number % f == 0]
        ans = random.choice(factors)
        wrong = [n for n in range(2, number) if number % n != 0]
        random.shuffle(wrong)
        prompt = f"Which number is a FACTOR of {number}?"
        expression = f"factor of {number}"
    else:
        base = random.randint(3, 9)
        ans = base * random.randint(2, 9)
        wrong = [n for n in range(base * 2, base * 10) if n % base != 0]
        random.shuffle(wrong)
        prompt = f"Which number is a MULTIPLE of {base}?"
        expression = f"multiple of {base}"

    options = [str(ans)] + [str(w) for w in wrong[:2]]
    random.shuffle(options)

    return _build(
        mode="factors_multiples",
        hint=(f"A factor goes into {number} with nothing left over." if "FACTOR" in prompt
              else f"A multiple of {base} is in the {base} times table: {base} x 1, {base} x 2, …"),
        expression=expression,
        prompt_text=prompt,
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _take_away_in_steps(a: int, b: int) -> str:
    """Subtract by place value: 245 - 132 is 245 - 100 - 30 - 2."""
    steps = [str(part) for part in (b // 100 * 100, b // 10 % 10 * 10, b % 10) if part]
    if len(steps) == 1:
        return f"Count back {b} from {a}."
    return f"Take {b} away from {a} in steps: " + ", then ".join(steps) + "."


def _think_backwards(op: str, b: int, result: int) -> str:
    undo = {"+": "-", "-": "+", "x": "\u00F7"}[op]
    return f"Think backwards: {result} {undo} {b} = ?"


def _same_bottom_hint(name1: str, name2: str) -> str:
    """Rewrite both fractions over a common denominator."""
    from math import lcm
    (n1, d1), (n2, d2) = (map(int, n.split("/")) for n in (name1, name2))
    common = lcm(d1, d2)
    return (f"Make the bottoms match: {name1} = {n1 * common // d1}/{common}, "
            f"{name2} = {n2 * common // d2}/{common}. Which top is bigger?")


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
           correct_answer: str, options: list[str], hint: str | None = None) -> dict:
    """`hint` is the worked first step shown after a miss; it must not give
    the answer away, since the question comes back later in the session."""
    prompt_data = json.dumps({
        "mode": mode,
        "expression": expression,
        "prompt_text": prompt_text,
        "prompt_image": prompt_image,
        "correct_answer": correct_answer,
        "hint": hint,
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
    "place_value": _gen_place_value,
    "rounding": _gen_rounding,
    "fraction_of_amount": _gen_fraction_of_amount,
    "equivalent_fractions": _gen_equivalent_fractions,
    "factors_multiples": _gen_factors_multiples,
}


def generate_math_question(mode: str) -> dict:
    """Generate a single question in a named mode.

    Used by the topic spine, which decides *what* to practise and then asks for
    one question of the matching mode.
    """
    generator = _GENERATORS.get(mode)
    if generator is None:
        raise ValueError(f"Unknown math question mode: {mode}")
    return generator()


def available_modes() -> set[str]:
    return set(_GENERATORS)
