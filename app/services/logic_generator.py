import json
import random


def generate_logic_questions(age: int, count: int = 5) -> list[dict]:
    """Generate age-appropriate logic questions.

    Returns list of dicts with: mode, expression, prompt_text, prompt_image,
    correct_answer, options, prompt_data (JSON string).
    """
    if age <= 5:
        modes = ["pattern_next", "odd_one_out", "size_order", "matching_pairs",
                 "color_match", "counting_objects"]
        weights = [20, 20, 15, 15, 15, 15]
    elif age >= 8:
        # Grade 3-4 level: harder reasoning, multi-step, deduction
        modes = ["number_pattern_hard", "analogy_hard", "logic_deduction",
                 "matrix_pattern", "word_analogy", "sequence_hard",
                 "odd_one_out_hard", "comparison"]
        weights = [15, 15, 15, 15, 12, 12, 8, 8]
    else:
        # Grade 2 level: mix visual modes with intermediate reasoning modes
        modes = ["pattern_next", "odd_one_out", "number_pattern", "analogy",
                 "sequence_completion", "comparison", "before_after"]
        weights = [15, 15, 15, 15, 15, 15, 10]

    questions = []
    for _ in range(count):
        mode = random.choices(modes, weights=weights, k=1)[0]
        q = _GENERATORS[mode]()
        questions.append(q)
    return questions


# ── Young kids (age <= 5) ──

_COLOR_EMOJIS = [
    ("🔴", "🔵"), ("🟢", "🟡"), ("🔴", "🟢"), ("🔵", "🟡"),
    ("🟠", "🟣"), ("⭐", "🌙"), ("🌸", "🍀"), ("🔵", "🟠"),
    ("🍎", "🍊"), ("❤️", "💙"), ("🌸", "⭐"), ("🎈", "🎀"),
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
    (["👕", "👗", "🧥"], "🍌", "clothes"),
    (["🔨", "🪛", "🔧"], "🐱", "tools"),
    (["🌧️", "⛈️", "🌪️"], "🎸", "weather"),
    (["🧃", "🥛", "☕"], "👟", "drinks"),
    (["🐙", "🦀", "🐠"], "🌳", "sea creatures"),
    (["🏠", "🏢", "⛪"], "🍎", "buildings"),
    (["🔴", "🔵", "🟢"], "🐶", "colors"),
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
        hint=f"Three of these are {category}. Which one isn't?",
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
    (["✈️", "🚗", "🚲"], "✈️"),   # airplane biggest
    (["🏔️", "🏠", "🪨"], "🏔️"),  # mountain biggest
    (["☀️", "🌍", "🌙"], "☀️"),   # sun biggest
    (["🦕", "🐊", "🦎"], "🦕"),   # dinosaur biggest
    (["🚢", "🚤", "🛶"], "🚢"),   # ship biggest
    (["🍉", "🍊", "🍇"], "🍉"),   # watermelon biggest
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
    ("🧤", "🧣", ["🧣", "🍦", "🎸"]),
    ("👟", "🧦", ["🧦", "🧤", "🎒"]),
    ("🍞", "🧈", ["🧈", "🖊️", "⚽"]),
    ("☀️", "🕶️", ["🕶️", "🧤", "🎸"]),
    ("🌧️", "☂️", ["☂️", "🕶️", "🧣"]),
    ("✏️", "📄", ["📄", "🍎", "🎸"]),
    ("🔑", "🔒", ["🔒", "📱", "🎈"]),
    ("🖌️", "🎨", ["🎨", "🔑", "🧦"]),
    ("🥣", "🥄", ["🥄", "🚗", "🎸"]),
    ("🔨", "🪵", ["🪵", "🍎", "🧦"]),
    ("🐶", "🦴", ["🦴", "🎸", "🎩"]),
    ("🔥", "💧", ["💧", "⭐", "🎈"]),
    ("🪥", "🦷", ["🦷", "📄", "🚌"]),
    ("🎣", "🐟", ["🐟", "🐶", "🔑"]),
    ("📷", "🖼️", ["🖼️", "🧣", "⚽"]),
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


_COLOR_MATCH_GROUPS = [
    ("red", "🍎", ["🌹", "🌻", "🐸"]),
    ("red", "🚗", ["❤️", "🔵", "🌿"]),
    ("yellow", "🌻", ["⭐", "🔴", "🟢"]),
    ("yellow", "⭐", ["🍌", "🍎", "🔵"]),
    ("green", "🐸", ["🌿", "🔴", "⭐"]),
    ("green", "🌿", ["🐸", "🌻", "❤️"]),
    ("blue", "🔵", ["💙", "🍎", "🌻"]),
    ("blue", "💧", ["🔵", "🌹", "⭐"]),
    ("orange", "🍊", ["🥕", "🔵", "🌿"]),
    ("pink", "🌸", ["🎀", "🟢", "⭐"]),
]

def _gen_color_match() -> dict:
    color, prompt_emoji, opts = random.choice(_COLOR_MATCH_GROUPS)
    correct = opts[0]
    expression = prompt_emoji
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="color_match",
        expression=expression,
        prompt_text="Which is the same color?",
        prompt_image=prompt_emoji,
        correct_answer=correct,
        options=options,
    )


def _gen_counting_objects() -> dict:
    targets = ["🐶", "🐱", "🐟", "⭐", "🍎", "🌸", "🎈", "🐸"]
    distractors = ["🐶", "🐱", "🐟", "⭐", "🍎", "🌸", "🎈", "🐸"]
    target = random.choice(targets)
    distractor = random.choice([d for d in distractors if d != target])
    target_count = random.randint(2, 5)
    distractor_count = random.randint(2, 4)
    items = [target] * target_count + [distractor] * distractor_count
    random.shuffle(items)
    expression = "".join(items)
    prompt_text = "How many " + target + "?"
    options = _make_num_distractors_list(target_count)
    return _build(
        mode="counting_objects",
        expression=expression,
        prompt_text=prompt_text,
        prompt_image=expression,
        correct_answer=str(target_count),
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
    ("Day", "Night", "Sun", "Moon", ["Moon", "Rain", "Cloud"]),
    ("Up", "Down", "Left", "Right", ["Right", "Back", "Over"]),
    ("Happy", "Sad", "Light", "Dark", ["Dark", "Bright", "Soft"]),
    ("Cat", "Kitten", "Dog", "Puppy", ["Puppy", "Bone", "Bark"]),
    ("Bird", "Fly", "Fish", "Swim", ["Swim", "Walk", "Run"]),
    ("Open", "Close", "On", "Off", ["Off", "Up", "In"]),
    ("Hand", "Glove", "Foot", "Shoe", ["Shoe", "Hat", "Scarf"]),
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


def _gen_sequence_completion() -> dict:
    seq_type = random.choice(["aabb", "abc", "growing"])
    if seq_type == "aabb":
        pair = random.choice(_COLOR_EMOJIS)
        a, b = pair
        # AABB pattern: AABBAABB?  → next is determined by position
        pattern = [a, a, b, b, a, a]
        correct = b
        wrong = a
        others = ["⬛", "⬜", "🔶", "🔷", "💜", "💚"]
        third = random.choice([e for e in others if e != correct and e != wrong])
        expression = "".join(pattern) + " ?"
        options = [correct, wrong, third]
    elif seq_type == "abc":
        emojis = ["🔴", "🔵", "🟢", "🟡", "🟠", "🟣"]
        trio = random.sample(emojis, 3)
        a, b, c = trio
        pattern = [a, b, c, a, b]
        correct = c
        wrong_pool = [e for e in emojis if e not in trio]
        wrong1 = wrong_pool[0]
        wrong2 = wrong_pool[1] if len(wrong_pool) > 1 else a
        expression = "".join(pattern) + " ?"
        options = [correct, wrong1, wrong2]
    else:
        # Growing: ⭐ ⭐⭐ ⭐⭐⭐ ?  → ⭐⭐⭐⭐
        emoji = random.choice(["⭐", "🔴", "🌸", "🎈"])
        start = random.randint(1, 2)
        seq = [emoji * (start + i) for i in range(3)]
        correct_str = emoji * (start + 3)
        expression = "  ".join(seq) + "  ?"
        wrong1 = emoji * (start + 2)
        wrong2 = emoji * (start + 4)
        options = [correct_str, wrong1, wrong2]
        correct = correct_str
    random.shuffle(options)
    return _build(
        mode="sequence_completion",
        expression=expression,
        prompt_text="What comes next?",
        prompt_image=expression,
        correct_answer=correct,
        options=options,
    )


_COMPARISON_SETS = [
    ("Which is the fastest?", ["🐆", "🐢", "🐇"], "🐆"),
    ("Which is the heaviest?", ["🐘", "🐱", "🐶"], "🐘"),
    ("Which is the tallest?", ["🏔️", "🌳", "🏠"], "🏔️"),
    ("Which is the slowest?", ["🐢", "🐇", "🐎"], "🐢"),
    ("Which is the hottest?", ["☀️", "🌙", "⛄"], "☀️"),
    ("Which is the coldest?", ["⛄", "☀️", "🌸"], "⛄"),
    ("Which is the loudest?", ["🦁", "🐱", "🐟"], "🦁"),
    ("Which is the smallest?", ["🐜", "🐶", "🐘"], "🐜"),
    ("Which is the longest?", ["🐍", "🐱", "🐸"], "🐍"),
    ("Which holds the most water?", ["🌊", "🥛", "💧"], "🌊"),
]

def _gen_comparison() -> dict:
    prompt, items, correct = random.choice(_COMPARISON_SETS)
    display = list(items)
    random.shuffle(display)
    expression = "  ".join(display)
    options = list(display)
    random.shuffle(options)
    return _build(
        mode="comparison",
        expression=expression,
        prompt_text=prompt,
        prompt_image=expression,
        correct_answer=correct,
        options=options,
    )


_BEFORE_AFTER_SETS = [
    ("What comes right after Tuesday?", "Wednesday", ["Wednesday", "Monday", "Friday"]),
    ("What comes right before summer?", "Spring", ["Spring", "Winter", "Fall"]),
    ("What comes right after 3rd?", "4th", ["4th", "2nd", "5th"]),
    ("What comes right before Wednesday?", "Tuesday", ["Tuesday", "Thursday", "Friday"]),
    ("What comes right after Saturday?", "Sunday", ["Sunday", "Friday", "Monday"]),
    ("What comes right after winter?", "Spring", ["Spring", "Summer", "Fall"]),
    ("What comes right before 5th?", "4th", ["4th", "6th", "3rd"]),
    ("What comes right after March?", "April", ["April", "February", "May"]),
    ("What comes right before Friday?", "Thursday", ["Thursday", "Saturday", "Wednesday"]),
    ("Which meal comes right after breakfast?", "Lunch", ["Lunch", "Dinner", "Supper"]),
]

def _gen_before_after() -> dict:
    prompt, correct, opts = random.choice(_BEFORE_AFTER_SETS)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="before_after",
        expression=prompt,
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


# ── Grade 3-4 (age >= 8) ──

def _gen_number_pattern_hard() -> dict:
    """Harder number patterns: multiply, double+add, skip-count, triangular."""
    pattern_type = random.choice(["multiply", "double_add", "skip_big", "square", "triangular"])
    if pattern_type == "multiply":
        base = random.randint(2, 5)
        multiplier = random.randint(2, 4)
        seq = [base * (multiplier ** i) for i in range(4)]
        ans = base * (multiplier ** 4)
    elif pattern_type == "double_add":
        start = random.randint(1, 5)
        add = random.randint(1, 3)
        seq = [start]
        for _ in range(3):
            seq.append(seq[-1] * 2 + add)
        ans = seq[-1] * 2 + add
    elif pattern_type == "skip_big":
        start = random.randint(5, 20)
        step = random.choice([5, 7, 9, 11])
        seq = [start + step * i for i in range(4)]
        ans = seq[-1] + step
    elif pattern_type == "square":
        start = random.randint(1, 5)
        seq = [(start + i) ** 2 for i in range(4)]
        ans = (start + 4) ** 2
    else:  # triangular: +1, +2, +3, +4...
        start = random.randint(1, 5)
        seq = [start]
        for i in range(1, 4):
            seq.append(seq[-1] + i + 1)
        ans = seq[-1] + 5

    display = ", ".join(str(n) for n in seq)
    expression = display + ", ?"
    options = _make_num_distractors_list(ans)
    return _build(
        mode="number_pattern_hard",
        expression=expression,
        prompt_text="What comes next?",
        prompt_image=None,
        correct_answer=str(ans),
        options=options,
    )


_ANALOGIES_HARD = [
    ("Finger", "Hand", "Toe", "Foot", ["Foot", "Leg", "Arm"]),
    ("Page", "Book", "Brick", "Wall", ["Wall", "Clay", "Window"]),
    ("Petal", "Flower", "Branch", "Tree", ["Tree", "Leaf", "Root"]),
    ("Player", "Team", "Student", "Class", ["Class", "Desk", "Teacher"]),
    ("Chapter", "Novel", "Scene", "Movie", ["Movie", "Popcorn", "Ticket"]),
    ("Spoke", "Wheel", "String", "Guitar", ["Guitar", "Drum", "Flute"]),
    ("Cub", "Bear", "Calf", "Cow", ["Cow", "Horse", "Sheep"]),
    ("Carpenter", "Wood", "Tailor", "Cloth", ["Cloth", "Stone", "Glass"]),
    ("Author", "Book", "Director", "Film", ["Film", "Painting", "Song"]),
    ("Engine", "Car", "Heart", "Body", ["Body", "Brain", "Blood"]),
    ("Feather", "Bird", "Scale", "Fish", ["Fish", "Dog", "Fur"]),
    ("Oar", "Boat", "Pedal", "Bicycle", ["Bicycle", "Kite", "Wheel"]),
]

def _gen_analogy_hard() -> dict:
    a, b, c, correct, opts = random.choice(_ANALOGIES_HARD)
    expression = f"{a} : {b} = {c} : ?"
    prompt = f"{a} is to {b} as {c} is to ?"
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="analogy_hard",
        expression=expression,
        prompt_text=prompt,
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_LOGIC_DEDUCTIONS = [
    ("All dogs are animals. Rex is a dog.", "Rex is an animal",
     ["Rex is an animal", "Rex is a cat", "Rex is not a dog"]),
    ("If it rains, the ground gets wet. It is raining.", "The ground is wet",
     ["The ground is wet", "The ground is dry", "It is sunny"]),
    ("All squares are rectangles. This shape is a square.", "It is a rectangle",
     ["It is a rectangle", "It is a circle", "It is a triangle"]),
    ("Tom is taller than Sam. Sam is taller than Ben.", "Tom is taller than Ben",
     ["Tom is taller than Ben", "Ben is taller than Tom", "Ben is the tallest"]),
    ("Every bird has feathers. A penguin is a bird.", "A penguin has feathers",
     ["A penguin has feathers", "A penguin can fly", "A penguin has fur"]),
    ("Mia is older than Zoe. Zoe is older than Lily.", "Mia is older than Lily",
     ["Mia is older than Lily", "Lily is older than Mia", "Lily is the oldest"]),
    ("All fish live in water. A goldfish is a fish.", "A goldfish lives in water",
     ["A goldfish lives in water", "A goldfish lives on land", "A goldfish can fly"]),
    ("Stones sink in water. This pebble is a stone.", "The pebble sinks",
     ["The pebble sinks", "The pebble floats", "The pebble melts"]),
    ("If you study, you learn. Emma studied all week.", "Emma learned something",
     ["Emma learned something", "Emma forgot everything", "Emma didn't study"]),
    ("Water freezes below 0°C. The puddle is at -5°C.", "The puddle will freeze",
     ["The puddle will freeze", "The puddle will boil", "The puddle gets warmer"]),
]

def _gen_logic_deduction() -> dict:
    premise, correct, opts = random.choice(_LOGIC_DEDUCTIONS)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="logic_deduction",
        expression=premise,
        prompt_text="What must be true?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_MATRIX_PATTERNS = [
    # (grid description, question, correct, options)
    ("🔴🔵🔴\n🔵🔴🔵\n🔴🔵 ?", "Complete the grid", "🔴",
     ["🔴", "🔵", "🟢"]),
    ("1  2  3\n4  5  6\n7  8  ?", "Complete the grid", "9",
     ["9", "10", "7"]),
    ("⬆️ ➡️ ⬇️\n➡️ ⬇️ ⬆️\n⬇️ ⬆️ ?", "Complete the pattern", "➡️",
     ["➡️", "⬆️", "⬇️"]),
    ("2  4  6\n3  6  9\n4  8  ?", "Complete the grid", "12",
     ["12", "10", "14"]),
    ("🌑 🌓 🌕\n🌕 🌑 🌓\n🌓 🌕 ?", "Complete the pattern", "🌑",
     ["🌑", "🌓", "🌕"]),
    ("A  C  E\nB  D  F\nC  E  ?", "Complete the grid", "G",
     ["G", "F", "H"]),
    ("10 20 30\n20 30 40\n30 40 ?", "Complete the grid", "50",
     ["50", "60", "45"]),
    ("🟢🔴🟢\n🔴🟢🔴\n🟢🔴 ?", "Complete the grid", "🟢",
     ["🟢", "🔴", "🟡"]),
]

def _gen_matrix_pattern() -> dict:
    grid, prompt, correct, opts = random.choice(_MATRIX_PATTERNS)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="matrix_pattern",
        expression=grid,
        prompt_text=prompt,
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_WORD_ANALOGIES = [
    ("Glove is to hand as sock is to ___", "foot", ["foot", "arm", "head"]),
    ("Bark is to dog as meow is to ___", "cat", ["cat", "bird", "fish"]),
    ("Pilot is to airplane as captain is to ___", "ship", ["ship", "car", "train"]),
    ("Eyes are to seeing as ears are to ___", "hearing", ["hearing", "smelling", "tasting"]),
    ("Knife is to cut as pen is to ___", "write", ["write", "eat", "sleep"]),
    ("Night is to moon as day is to ___", "sun", ["sun", "stars", "dreams"]),
    ("Library is to books as museum is to ___", "art", ["art", "food", "homework"]),
    ("Chef is to kitchen as teacher is to ___", "classroom", ["classroom", "hospital", "garage"]),
    ("Brush is to paint as needle is to ___", "sew", ["sew", "write", "cook"]),
    ("Winter is to cold as summer is to ___", "hot", ["hot", "snowy", "frozen"]),
    ("Milk is to cow as egg is to ___", "chicken", ["chicken", "pig", "horse"]),
    ("Keyboard is to type as microphone is to ___", "speak", ["speak", "read", "write"]),
]

def _gen_word_analogy() -> dict:
    prompt, correct, opts = random.choice(_WORD_ANALOGIES)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="word_analogy",
        expression=prompt,
        prompt_text="Complete the analogy",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_sequence_hard() -> dict:
    """Harder sequences: alternating operations, Fibonacci-like, decreasing."""
    seq_type = random.choice(["alternating", "fibonacci", "decreasing", "prime_skip"])
    if seq_type == "alternating":
        # +2, +3, +2, +3...
        a = random.randint(1, 3)
        b = random.randint(4, 6)
        start = random.randint(1, 10)
        seq = [start]
        for i in range(4):
            seq.append(seq[-1] + (a if i % 2 == 0 else b))
        correct = seq[-1] + (a if 4 % 2 == 0 else b)
        seq_display = seq
    elif seq_type == "fibonacci":
        a, b = random.randint(1, 3), random.randint(2, 5)
        seq = [a, b]
        for _ in range(3):
            seq.append(seq[-1] + seq[-2])
        correct = seq[-1] + seq[-2]
        seq_display = seq
    elif seq_type == "decreasing":
        start = random.randint(50, 100)
        step = random.choice([3, 5, 7, 9])
        seq = [start - step * i for i in range(5)]
        correct = seq[-1] - step
        seq_display = seq
    else:  # prime_skip: skip counting by primes
        primes_step = random.choice([2, 3, 5, 7])
        start = random.randint(1, 10)
        seq = [start + primes_step * i for i in range(5)]
        correct = seq[-1] + primes_step
        seq_display = seq

    display = ", ".join(str(n) for n in seq_display)
    expression = display + ", ?"
    options = _make_num_distractors_list(correct)
    return _build(
        mode="sequence_hard",
        expression=expression,
        prompt_text="What comes next?",
        prompt_image=None,
        correct_answer=str(correct),
        options=options,
    )


_ODD_ONE_OUT_HARD = [
    (["Mercury", "Venus", "Mars"], "Paris", "planets vs city"),
    (["Triangle", "Square", "Pentagon"], "Blue", "shapes vs color"),
    (["Violin", "Cello", "Guitar"], "Drum", "string vs percussion"),
    (["Oxygen", "Nitrogen", "Helium"], "Water", "elements vs compound"),
    (["Shakespeare", "Dickens", "Austen"], "Einstein", "authors vs scientist"),
    (["Atlantic", "Pacific", "Indian"], "Nile", "oceans vs river"),
    (["Tulip", "Rose", "Daisy"], "Oak", "flowers vs tree"),
    (["Emerald", "Ruby", "Sapphire"], "Gold", "gems vs metal"),
    (["Trumpet", "Trombone", "Tuba"], "Violin", "brass vs strings"),
    (["Simile", "Metaphor", "Alliteration"], "Addition", "literary vs math"),
    (["Hiking", "Swimming", "Cycling"], "Chess", "physical vs mental"),
    (["Jupiter", "Saturn", "Neptune"], "Moon", "planets vs satellite"),
]

def _gen_odd_one_out_hard() -> dict:
    group_items, odd, category = random.choice(_ODD_ONE_OUT_HARD)
    all_items = group_items + [odd]
    random.shuffle(all_items)
    expression = " · ".join(all_items)
    options = list(all_items)
    random.shuffle(options)
    return _build(
        mode="odd_one_out_hard",
        hint=f"Three of these are {category.split(' vs ')[0]}. Which one isn't?",
        expression=expression,
        prompt_text="Which one doesn't belong?",
        prompt_image=None,
        correct_answer=odd,
        options=options,
    )


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
    # Young kids (age <= 5)
    "pattern_next": _gen_pattern_next,
    "odd_one_out": _gen_odd_one_out,
    "size_order": _gen_size_order,
    "matching_pairs": _gen_matching_pairs,
    "color_match": _gen_color_match,
    "counting_objects": _gen_counting_objects,
    # Grade 2 (age 6-7)
    "number_pattern": _gen_number_pattern,
    "analogy": _gen_analogy,
    "sequence_completion": _gen_sequence_completion,
    "comparison": _gen_comparison,
    "before_after": _gen_before_after,
    # Grade 3-4 (age >= 8)
    "number_pattern_hard": _gen_number_pattern_hard,
    "analogy_hard": _gen_analogy_hard,
    "logic_deduction": _gen_logic_deduction,
    "matrix_pattern": _gen_matrix_pattern,
    "word_analogy": _gen_word_analogy,
    "sequence_hard": _gen_sequence_hard,
    "odd_one_out_hard": _gen_odd_one_out_hard,
}
