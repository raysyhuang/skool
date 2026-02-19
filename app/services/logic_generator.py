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
        # Grade 2 level: mix young-kid visual modes with simple older-kid modes
        modes = ["pattern_next", "odd_one_out", "number_pattern", "analogy"]
        weights = [25, 25, 25, 25]

    questions = []
    for _ in range(count):
        mode = random.choices(modes, weights=weights, k=1)[0]
        q = _GENERATORS[mode]()
        questions.append(q)
    return questions


# ── Young kids (age <= 5) ──

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
        prompt_text="Which one is different?",
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
        prompt_text=item + " goes with?",
        prompt_image=item,
        correct_answer=correct,
        options=options,
    )


# ── Older kids (age >= 6) — grade 2 level ──

def _gen_number_pattern() -> dict:
    # Simple arithmetic sequences only (no geometric/squares)
    start = random.randint(1, 10)
    step = random.randint(1, 3)
    seq = [start + step * i for i in range(4)]
    ans = seq[-1] + step

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
    ("Happy", "Sad", "Light", "Dark", ["Dark", "Bright", "Heavy"]),
    ("Cat", "Kitten", "Dog", "Puppy", ["Puppy", "Bone", "Bark"]),
    ("Bird", "Fly", "Fish", "Swim", ["Swim", "Walk", "Run"]),
    ("Open", "Close", "On", "Off", ["Off", "Up", "In"]),
    ("Hand", "Glove", "Foot", "Shoe", ["Shoe", "Hat", "Sock"]),
]

def _gen_analogy() -> dict:
    a, b, c, correct, opts = random.choice(_ANALOGIES)
    expression = a + " : " + b + " = " + c + " : ?"
    prompt = a + " is to " + b + " as " + c + " is to ?"
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="analogy",
        expression=expression,
        prompt_text=prompt,
        prompt_image=None,
        correct_answer=correct,
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
}
