import json
import random


def generate_logic_questions(age: int, count: int = 5) -> list[dict]:
    """Generate age-appropriate logic questions.

    Returns list of dicts with: mode, expression, prompt_text, prompt_image,
    correct_answer, options, prompt_data (JSON string).
    """
    if age <= 5:
        modes = ["pattern_next", "odd_one_out", "size_order", "matching_pairs"]
        weights = [30, 30, 20, 20]
    else:
        modes = ["number_pattern", "analogy", "comparison", "sequence_next"]
        weights = [30, 30, 20, 20]

    questions = []
    for _ in range(count):
        mode = random.choices(modes, weights=weights, k=1)[0]
        q = _GENERATORS[mode]()
        questions.append(q)
    return questions


# ── Young kids (age ≤ 5) ──

_COLOR_EMOJIS = [
    ("🔴", "🔵"), ("🟢", "🟡"), ("🔴", "🟢"), ("🔵", "🟡"),
    ("🟠", "🟣"), ("⭐", "🌙"), ("🌸", "🍀"),
]

def _gen_pattern_next() -> dict:
    pair = random.choice(_COLOR_EMOJIS)
    a, b = pair
    # Pattern: ABABAB?
    pattern_len = random.choice([4, 5, 6])
    pattern = []
    for i in range(pattern_len):
        pattern.append(a if i % 2 == 0 else b)
    # Next is determined by position
    correct = a if pattern_len % 2 == 0 else b
    wrong = b if correct == a else a
    expression = "".join(pattern) + " ?"
    # Third distractor from a different emoji
    others = ["⬛", "⬜", "🔶", "🔷", "💜", "💚"]
    third = random.choice([e for e in others if e != correct and e != wrong])
    options = [correct, wrong, third]
    random.shuffle(options)
    return _build(
        mode="pattern_next",
        expression=expression,
        prompt_text="What comes next?",
        prompt_image=expression,
        correct_answer=correct,
        options=options,
    )


_ODD_ONE_OUT_SETS = [
    (["🐶", "🐱", "🐟"], "🚗", "animals"),
    (["🍎", "🍊", "🍇"], "🚌", "fruits"),
    (["🚗", "🚌", "🚂"], "🐶", "vehicles"),
    (["⭐", "🌙", "☀️"], "🎈", "sky things"),
    (["👟", "👢", "🩴"], "🎩", "footwear"),
    (["🖊️", "✏️", "🖍️"], "🍕", "writing tools"),
    (["🎸", "🥁", "🎹"], "📚", "instruments"),
    (["🐘", "🦁", "🐻"], "✈️", "animals"),
    (["🍕", "🍔", "🌮"], "🎾", "food"),
    (["⚽", "🏀", "🎾"], "🌸", "balls"),
]

def _gen_odd_one_out() -> dict:
    group_items, odd, category = random.choice(_ODD_ONE_OUT_SETS)
    all_items = group_items + [odd]
    random.shuffle(all_items)
    expression = "  ".join(all_items)
    # Options: all 4 items, correct is the odd one
    options = list(all_items)
    random.shuffle(options)
    return _build(
        mode="odd_one_out",
        expression=expression,
        prompt_text="Which one doesn't belong?",
        prompt_image=expression,
        correct_answer=odd,
        options=options,
    )


_SIZE_SETS = [
    (["🐘", "🐶", "🐱"], "🐘"),  # elephant biggest
    (["🐋", "🐟", "🦐"], "🐋"),  # whale biggest
    (["🏠", "🏢", "⛺"], "🏢"),   # building biggest
    (["🌳", "🌿", "🍀"], "🌳"),   # tree biggest
    (["🚌", "🚗", "🛵"], "🚌"),   # bus biggest
    (["🦁", "🐱", "🐭"], "🦁"),   # lion biggest
]

def _gen_size_order() -> dict:
    items, biggest = random.choice(_SIZE_SETS)
    display = list(items)
    random.shuffle(display)
    expression = "  ".join(display)
    options = list(display)
    random.shuffle(options)
    return _build(
        mode="size_order",
        expression=expression,
        prompt_text="Which is the biggest?",
        prompt_image=expression,
        correct_answer=biggest,
        options=options,
    )


_MATCHING_PAIRS = [
    ("🧤", "🧣", ["🧣", "🎩", "👟"]),
    ("👟", "🧦", ["🧦", "🧤", "🎒"]),
    ("🍞", "🧈", ["🧈", "🖊️", "⚽"]),
    ("☀️", "🕶️", ["🕶️", "🧤", "☂️"]),
    ("🌧️", "☂️", ["☂️", "🕶️", "🧣"]),
    ("✏️", "📄", ["📄", "🍎", "🎸"]),
    ("🔑", "🔒", ["🔒", "📱", "🎈"]),
    ("🖌️", "🎨", ["🎨", "🔑", "🧦"]),
]

def _gen_matching_pairs() -> dict:
    item, correct, opts = random.choice(_MATCHING_PAIRS)
    expression = item + " goes with ?"
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="matching_pairs",
        expression=expression,
        prompt_text=f"{item} goes with?",
        prompt_image=item,
        correct_answer=correct,
        options=options,
    )


# ── Older kids (age ≥ 6) ──

def _gen_number_pattern() -> dict:
    pattern_type = random.choice(["arithmetic", "geometric", "squares"])
    if pattern_type == "arithmetic":
        start = random.randint(1, 20)
        step = random.randint(2, 5)
        seq = [start + step * i for i in range(5)]
        ans = seq[-1] + step
    elif pattern_type == "geometric":
        start = random.randint(1, 4)
        ratio = random.choice([2, 3])
        seq = [start * (ratio ** i) for i in range(5)]
        ans = seq[-1] * ratio
    else:
        start = random.randint(1, 5)
        seq = [(start + i) ** 2 for i in range(5)]
        ans = (start + 5) ** 2

    display = ", ".join(str(n) for n in seq)
    expression = display + ", ?"
    options = _make_num_distractors_list(ans)
    return _build(
        mode="number_pattern",
        expression=expression,
        prompt_text="What comes next?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


_ANALOGIES = [
    ("Hot", "Cold", "Big", "Small", ["Small", "Fast", "Tall"]),
    ("Day", "Night", "Sun", "Moon", ["Moon", "Star", "Cloud"]),
    ("Up", "Down", "Left", "Right", ["Right", "Back", "Over"]),
    ("Fast", "Slow", "Loud", "Quiet", ["Quiet", "Soft", "Dark"]),
    ("Happy", "Sad", "Light", "Dark", ["Dark", "Bright", "Heavy"]),
    ("Cat", "Kitten", "Dog", "Puppy", ["Puppy", "Bone", "Bark"]),
    ("Water", "Ice", "Rain", "Snow", ["Snow", "Cloud", "Fog"]),
    ("Fire", "Hot", "Ice", "Cold", ["Cold", "White", "Hard"]),
    ("Book", "Read", "Song", "Sing", ["Sing", "Dance", "Write"]),
    ("Bird", "Fly", "Fish", "Swim", ["Swim", "Walk", "Run"]),
]

def _gen_analogy() -> dict:
    a, b, c, correct, opts = random.choice(_ANALOGIES)
    expression = f"{a} is to {b} as {c} is to ?"
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="analogy",
        expression=expression,
        prompt_text=expression,
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_NAMES = ["Alex", "Sam", "Jo"]

def _gen_comparison() -> dict:
    names = random.sample(_NAMES, 3)
    a, b, c = names
    # A > B > C — who is biggest?
    expression = f"{a} > {b} and {b} > {c}"
    prompt_text = f"If {a} > {b} and {b} > {c}, which is biggest?"
    options = list(names)
    random.shuffle(options)
    return _build(
        mode="comparison",
        expression=expression,
        prompt_text=prompt_text,
        prompt_image=None,
        correct_answer=a,
        options=options,
    )


def _gen_sequence_next() -> dict:
    seq_type = random.choice(["fibonacci", "doubling", "triangular"])
    if seq_type == "fibonacci":
        seq = [1, 1, 2, 3, 5]
        ans = 8
    elif seq_type == "doubling":
        start = random.choice([1, 2, 3])
        seq = [start * (2 ** i) for i in range(5)]
        ans = seq[-1] * 2
    else:
        # Triangular: 1, 3, 6, 10, 15, 21
        seq = [n * (n + 1) // 2 for n in range(1, 6)]
        ans = 6 * 7 // 2  # 21

    display = ", ".join(str(n) for n in seq)
    expression = display + ", ?"
    options = _make_num_distractors_list(ans)
    return _build(
        mode="sequence_next",
        expression=expression,
        prompt_text="What comes next?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


def _make_num_distractors_list(correct: int) -> list[str]:
    """Generate 2 plausible distractors near the correct answer."""
    distractors = set()
    offsets = [-3, -2, -1, 1, 2, 3]
    random.shuffle(offsets)
    for off in offsets:
        d = correct + off
        if d != correct and d >= 0:
            distractors.add(d)
        if len(distractors) >= 2:
            break
    while len(distractors) < 2:
        d = correct + random.choice([4, 5, -4, -5])
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
    "pattern_next": _gen_pattern_next,
    "odd_one_out": _gen_odd_one_out,
    "size_order": _gen_size_order,
    "matching_pairs": _gen_matching_pairs,
    "number_pattern": _gen_number_pattern,
    "analogy": _gen_analogy,
    "comparison": _gen_comparison,
    "sequence_next": _gen_sequence_next,
}
