import json
import random
from pathlib import Path

# Real words a random letter edit of a sight word can produce ("then" ->
# "than", "on" -> "no"). Offered as a "wrong spelling" they'd be correct, or
# worse. Rebuild with scripts/build_spelling_blocklist.py after editing the
# sight-word lists.
_REAL_WORDS = frozenset(
    (Path(__file__).with_name("spelling_blocklist.txt")).read_text().split()
)


# ── Content pools ──

# Letter-sound pairs for phonics (age 4-5)
_LETTER_SOUNDS = {
    "A": ("ah", "🍎 apple"),
    "B": ("buh", "🐻 bear"),
    "C": ("kuh", "🐱 cat"),
    "D": ("duh", "🐶 dog"),
    "E": ("eh", "🥚 egg"),
    "F": ("fff", "🐟 fish"),
    "G": ("guh", "🍇 grapes"),
    "H": ("huh", "🏠 house"),
    "I": ("ih", "🦎 iguana"),
    "J": ("juh", "🧃 juice"),
    "K": ("kuh", "🪁 kite"),
    "L": ("lll", "🦁 lion"),
    "M": ("mmm", "🌙 moon"),
    "N": ("nnn", "👃 nose"),
    "O": ("ah/oh", "🐙 octopus"),
    "P": ("puh", "🐷 pig"),
    "R": ("rrr", "🐰 rabbit"),
    "S": ("sss", "☀️ sun"),
    "T": ("tuh", "🐢 turtle"),
}

# Beginning sound matching: word → first letter
_BEGINNING_SOUNDS = [
    ("🍎 apple", "A"), ("🐻 bear", "B"), ("🐱 cat", "C"),
    ("🐶 dog", "D"), ("🐟 fish", "F"), ("🍇 grapes", "G"),
    ("🏠 house", "H"), ("🧃 juice", "J"), ("🪁 kite", "K"),
    ("🦁 lion", "L"), ("🌙 moon", "M"), ("👃 nose", "N"),
    ("🐷 pig", "P"), ("🐰 rabbit", "R"), ("☀️ sun", "S"),
    ("🐢 turtle", "T"), ("🥚 egg", "E"),
]

# Rhyming word groups for age 4-5
_RHYME_GROUPS = [
    ("cat", ["bat", "hat", "mat", "rat", "sat"]),
    ("dog", ["fog", "hog", "log", "jog"]),
    ("sun", ["bun", "fun", "run", "gun"]),
    ("red", ["bed", "fed", "led", "Ted"]),
    ("big", ["dig", "fig", "pig", "wig"]),
    ("hop", ["mop", "pop", "top", "cop"]),
    ("hen", ["den", "men", "pen", "ten"]),
    ("bug", ["hug", "mug", "rug", "tug"]),
    ("can", ["fan", "man", "pan", "van"]),
    ("sit", ["bit", "fit", "hit", "kit"]),
]

# ── Pools for the grammar modes added to widen taxonomy coverage ──

# Plurals where a plain -s is wrong: true irregulars (child/children) plus
# the -ies and -es patterns children reach for -s on anyway.
_IRREGULAR_PLURALS = [
    ("child", "children"), ("foot", "feet"), ("tooth", "teeth"),
    ("mouse", "mice"), ("goose", "geese"), ("man", "men"),
    ("woman", "women"), ("leaf", "leaves"),
    ("knife", "knives"), ("wolf", "wolves"), ("shelf", "shelves"),
    ("baby", "babies"), ("city", "cities"), ("story", "stories"),
    ("box", "boxes"), ("bus", "buses"), ("dish", "dishes"),
]

# Irregular past tense: same idea for -ed.
_IRREGULAR_PAST = [
    ("go", "went"), ("eat", "ate"), ("run", "ran"), ("see", "saw"),
    ("take", "took"), ("give", "gave"), ("come", "came"), ("bring", "brought"),
    ("think", "thought"), ("catch", "caught"), ("teach", "taught"),
    ("buy", "bought"), ("write", "wrote"), ("sing", "sang"),
    ("drink", "drank"), ("swim", "swam"), ("fly", "flew"), ("draw", "drew"),
]

# Syllable counts, chosen so the split is unambiguous when said aloud.
_SYLLABLE_WORDS = [
    ("cat", 1), ("dog", 1), ("book", 1), ("tree", 1),
    ("rabbit", 2), ("pencil", 2), ("garden", 2), ("window", 2), ("monkey", 2),
    ("elephant", 3), ("banana", 3), ("computer", 3), ("umbrella", 3),
    ("butterfly", 3), ("dinosaur", 3),
    ("caterpillar", 4), ("television", 4), ("alligator", 4),
]

# Sight words by tier (Dolch + Fry common words)
_SIGHT_WORDS_EASY = [
    "the", "and", "to", "is", "in", "it", "he", "she", "my",
    "we", "on", "at", "do", "no", "go", "so", "up", "am", "an",
    "me", "be", "us", "or", "by", "if",
]

_SIGHT_WORDS_MEDIUM = [
    "said", "was", "are", "you", "they", "have", "from", "this",
    "that", "with", "what", "when", "were", "there", "your", "been",
    "many", "some", "very", "after", "know", "just", "than", "them",
    "could", "would", "about", "other", "which", "their", "first",
]

# Vocabulary: word → definition (age 8+)
_VOCABULARY = [
    ("enormous", "very very big"),
    ("tiny", "very very small"),
    ("brave", "not afraid"),
    ("journey", "a long trip"),
    ("ancient", "very very old"),
    ("discover", "to find something new"),
    ("fragile", "easy to break"),
    ("furious", "very angry"),
    ("brilliant", "very smart or bright"),
    ("curious", "wanting to know more"),
    ("generous", "likes to share and give"),
    ("delicious", "tastes very good"),
    ("exhausted", "very very tired"),
    ("terrified", "very scared"),
    ("complicated", "hard to understand"),
    ("magnificent", "very beautiful or grand"),
    ("mysterious", "full of secrets"),
    ("ordinary", "normal, not special"),
    ("peculiar", "strange or unusual"),
    ("valuable", "worth a lot"),
]

# Antonym pairs (age 8+)
_ANTONYMS = [
    ("hot", "cold"), ("big", "small"), ("fast", "slow"),
    ("happy", "sad"), ("light", "dark"), ("up", "down"),
    ("loud", "quiet"), ("hard", "soft"), ("old", "new"),
    ("tall", "short"), ("wet", "dry"), ("open", "shut"),
    ("empty", "full"), ("early", "late"), ("near", "far"),
    ("rich", "poor"), ("strong", "weak"), ("thick", "thin"),
]

# Words from other pairs that are also a fair opposite of the key word, so
# they can't be offered as wrong answers for it
_ALSO_OPPOSITE = {"loud": {"soft"}, "soft": {"loud"}}

# Prefix/suffix patterns (age 8+)
_PREFIX_SUFFIX = [
    ("un + happy", "unhappy", "not happy"),
    ("re + write", "rewrite", "write again"),
    ("un + kind", "unkind", "not kind"),
    ("re + build", "rebuild", "build again"),
    ("pre + heat", "preheat", "heat before"),
    ("un + fair", "unfair", "not fair"),
    ("re + read", "reread", "read again"),
    ("dis + agree", "disagree", "not agree"),
    ("mis + spell", "misspell", "spell wrong"),
    ("re + play", "replay", "play again"),
    ("un + lock", "unlock", "open the lock"),
    ("dis + like", "dislike", "not like"),
]

# CVC words for blending (age 4-5)
_CVC_WORDS = [
    ("c-a-t", "cat", "🐱"), ("d-o-g", "dog", "🐶"),
    ("s-u-n", "sun", "☀️"), ("b-u-s", "bus", "🚌"),
    ("h-a-t", "hat", "🎩"), ("c-u-p", "cup", "🥤"),
    ("b-e-d", "bed", "🛏️"), ("p-i-g", "pig", "🐷"),
    ("r-u-n", "run", "🏃"), ("f-i-n", "fin", "🐠"),
    ("m-a-p", "map", "🗺️"), ("p-a-n", "pan", "🍳"),
    ("b-a-t", "bat", "🦇"), ("j-a-m", "jam", "🫙"),
    ("p-e-n", "pen", "🖊️"), ("h-e-n", "hen", "🐔"),
]


def generate_english_questions(age: int, count: int = 5) -> list[dict]:
    """Generate age-appropriate English language questions."""
    if age <= 5:
        modes = [
            "letter_sound", "beginning_sound", "rhyme_match", "cvc_blend",
        ]
        weights = [30, 30, 20, 20]
    elif age >= 8:
        # Grade 3-4: harder vocab, context clues, homophones, synonyms
        modes = [
            "vocabulary_hard", "context_clues", "homophone_pick",
            "synonym_match", "prefix_suffix_hard", "sentence_complete",
            "plural_form", "past_tense",
        ]
        weights = [14, 15, 12, 12, 12, 12, 11, 12]
    else:
        modes = [
            "sight_word_spell", "vocabulary_match", "antonym_match",
            "prefix_suffix", "rhyme_match", "syllable_count", "plural_form",
        ]
        weights = [20, 20, 15, 15, 8, 11, 11]

    questions = []
    for _ in range(count):
        mode = random.choices(modes, weights=weights, k=1)[0]
        q = _GENERATORS[mode](age)
        questions.append(q)
    return questions


# ── Young kids (age <= 5) ──

def _gen_letter_sound(age: int) -> dict:
    """What sound does this letter make?"""
    letter, (sound, example) = random.choice(list(_LETTER_SOUNDS.items()))
    correct = f"{sound}  ({example})"

    # Distractors: sounds from other letters. Skip any that share a sound
    # with the answer (C and K are both "kuh"), or both would be right.
    sounds = set(sound.split("/"))
    others = [v for k, v in _LETTER_SOUNDS.items()
              if k != letter and not sounds & set(v[0].split("/"))]
    random.shuffle(others)
    distractors = [f"{s}  ({ex})" for s, ex in others[:2]]

    options = [correct] + distractors
    random.shuffle(options)

    return _build(
        mode="letter_sound",
        expression=letter,
        prompt_text=f"What sound does '{letter}' make?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_beginning_sound(age: int) -> dict:
    """What letter does this word start with?"""
    word_img, correct_letter = random.choice(_BEGINNING_SOUNDS)

    all_letters = list({l for _, l in _BEGINNING_SOUNDS if l != correct_letter})
    random.shuffle(all_letters)
    distractors = all_letters[:2]

    options = [correct_letter] + distractors
    random.shuffle(options)

    return _build(
        mode="beginning_sound",
        expression=word_img,
        prompt_text=f"What letter does it start with?",
        prompt_image=word_img,
        correct_answer=correct_letter,
        options=options,
    )


def _gen_rhyme_match(age: int) -> dict:
    """Which word rhymes with the given word?"""
    base_word, rhymes = random.choice(_RHYME_GROUPS)
    correct = random.choice(rhymes)

    # Distractors: words from other rhyme groups
    other_words = []
    for w, rh in _RHYME_GROUPS:
        if w != base_word:
            other_words.extend(rh[:1])
    random.shuffle(other_words)
    distractors = [w for w in other_words if w != correct][:2]

    options = [correct] + distractors
    random.shuffle(options)

    return _build(
        mode="rhyme_match",
        expression=f"🎵 {base_word}",
        prompt_text=f"Which word rhymes with '{base_word}'?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_cvc_blend(age: int) -> dict:
    """Blend these sounds together — what word?"""
    sounds, word, emoji = random.choice(_CVC_WORDS)
    correct = f"{word} {emoji}"

    # Distractors from other CVC words
    others = [(w, e) for s, w, e in _CVC_WORDS if w != word]
    random.shuffle(others)
    distractors = [f"{w} {e}" for w, e in others[:2]]

    options = [correct] + distractors
    random.shuffle(options)

    return _build(
        mode="cvc_blend",
        expression=sounds,
        prompt_text="Blend the sounds! What word?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


# ── Older kids (age >= 6) ──

def _gen_sight_word_spell(age: int) -> dict:
    """Pick the correctly spelled sight word."""
    pool = _SIGHT_WORDS_MEDIUM if age >= 7 else _SIGHT_WORDS_EASY
    word = random.choice(pool)
    correct = word

    # Generate plausible misspellings
    misspellings = _make_misspellings(word, 2)

    options = [correct] + misspellings
    random.shuffle(options)

    return _build(
        mode="sight_word_spell",
        expression=f"📖 {word}",
        prompt_text=f"Which spelling is correct?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_vocabulary_match(age: int) -> dict:
    """Match the word to its meaning."""
    # Deduplicate vocabulary
    seen = set()
    pool = []
    for w, d in _VOCABULARY:
        if w not in seen:
            seen.add(w)
            pool.append((w, d))

    word, definition = random.choice(pool)
    correct = definition

    # Distractors: definitions of other words
    other_defs = [d for w2, d in pool if w2 != word]
    random.shuffle(other_defs)
    distractors = other_defs[:2]

    options = [correct] + distractors
    random.shuffle(options)

    return _build(
        mode="vocabulary_match",
        expression=f"📚 {word}",
        prompt_text=f"What does '{word}' mean?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_antonym_match(age: int) -> dict:
    """What is the opposite of this word?"""
    pair = random.choice(_ANTONYMS)
    # Randomly pick which word to show
    if random.random() < 0.5:
        shown, correct = pair
    else:
        correct, shown = pair

    # Distractors: other words (not the answer or the shown word)
    all_words = set()
    for a, b in _ANTONYMS:
        all_words.add(a)
        all_words.add(b)
    all_words.discard(correct)
    all_words.discard(shown)
    all_words -= _ALSO_OPPOSITE.get(shown, set())
    distractors = random.sample(list(all_words), min(2, len(all_words)))

    options = [correct] + distractors
    random.shuffle(options)

    return _build(
        mode="antonym_match",
        expression=f"⬅️➡️ {shown}",
        prompt_text=f"What is the OPPOSITE of '{shown}'?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


def _gen_prefix_suffix(age: int) -> dict:
    """What word do you get when you add this prefix?"""
    parts, combined, meaning = random.choice(_PREFIX_SUFFIX)
    correct = combined

    # Distractors: other combined words
    others = [c for p, c, m in _PREFIX_SUFFIX if c != combined]
    random.shuffle(others)
    distractors = others[:2]

    options = [correct] + distractors
    random.shuffle(options)

    return _build(
        mode="prefix_suffix",
        expression=parts,
        prompt_text=f"Put them together! ({meaning})",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


# ── Grade 3-4 (age >= 8) ──

_VOCABULARY_HARD = [
    ("consequence", "what happens because of something"),
    ("ambitious", "having big goals"),
    ("reluctant", "not wanting to do something"),
    ("persevere", "to keep trying even when it's hard"),
    ("abundant", "having a lot of something"),
    ("cautious", "being very careful"),
    ("contradict", "to say the opposite"),
    ("demonstrate", "to show how something works"),
    ("exaggerate", "to make something sound bigger than it is"),
    ("genuine", "real and not fake"),
    ("hesitate", "to pause before doing something"),
    ("inevitable", "sure to happen"),
    ("observe", "to watch carefully"),
    ("predict", "to guess what will happen next"),
    ("sufficient", "enough, as much as needed"),
    ("resemble", "to look like something else"),
    ("sympathy", "feeling sorry for someone"),
    ("temporary", "lasting only a short time"),
    ("urgent", "needing attention right now"),
    ("vivid", "very bright and clear"),
]

def _gen_plural_form(age: int) -> dict:
    """Irregular plurals — where the regular -s rule fails."""
    singular, plural = random.choice(_IRREGULAR_PLURALS)

    # Distractors are the mistakes a child actually makes: the naive -s form,
    # and another word's plural.
    naive = singular + "s"
    others = [p for _, p in _IRREGULAR_PLURALS if p != plural and p != naive]
    wrong = [naive, random.choice(others)]

    options = [plural] + wrong
    random.shuffle(options)

    return _build(
        mode="plural_form",
        expression=f"one {singular} \u2192 two ___",
        prompt_text=f"One {singular}, two ___?",
        prompt_image=None,
        correct_answer=plural,
        options=options,
    )


def _gen_past_tense(age: int) -> dict:
    """Irregular past tense — where the regular -ed rule fails."""
    present, past = random.choice(_IRREGULAR_PAST)

    naive = present + ("d" if present.endswith("e") else "ed")
    others = [p for _, p in _IRREGULAR_PAST if p != past and p != naive]
    wrong = [naive, random.choice(others)]

    options = [past] + wrong
    random.shuffle(options)

    return _build(
        mode="past_tense",
        expression=f"today I {present} \u2192 yesterday I ___",
        prompt_text=f"Today I {present}. Yesterday I ___?",
        prompt_image=None,
        correct_answer=past,
        options=options,
    )


def _gen_syllable_count(age: int) -> dict:
    """How many beats in the word? Underpins reading longer words."""
    word, count = random.choice(_SYLLABLE_WORDS)

    wrong = set()
    for delta in (-2, -1, 1, 2):
        candidate = count + delta
        if candidate >= 1 and candidate != count:
            wrong.add(candidate)
    wrong = random.sample(sorted(wrong), 2)

    options = [str(count)] + [str(w) for w in wrong]
    random.shuffle(options)

    return _build(
        mode="syllable_count",
        expression=f"\U0001F44F {word}",
        prompt_text=f"How many syllables in '{word}'?",
        prompt_image=None,
        correct_answer=str(count),
        options=options,
    )


def _gen_vocabulary_hard(age: int) -> dict:
    word, definition = random.choice(_VOCABULARY_HARD)
    correct = definition
    other_defs = [d for w, d in _VOCABULARY_HARD if w != word]
    random.shuffle(other_defs)
    distractors = other_defs[:2]
    options = [correct] + distractors
    random.shuffle(options)
    return _build(
        mode="vocabulary_hard",
        expression=f"📚 {word}",
        prompt_text=f"What does '{word}' mean?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_CONTEXT_CLUES = [
    ("The food was so ___ that everyone asked for seconds.", "delicious",
     ["delicious", "disgusting", "tiny"]),
    ("She felt ___ after running the whole race without stopping.", "exhausted",
     ["exhausted", "energetic", "confused"]),
    ("The magician's trick was so ___ that nobody could figure it out.", "mysterious",
     ["mysterious", "obvious", "boring"]),
    ("Be ___ when carrying the glass vase — it could break easily.", "careful",
     ["careful", "careless", "quick"]),
    ("The sunset was ___, with bright oranges and pinks filling the sky.", "spectacular",
     ["spectacular", "dull", "scary"]),
    ("He was ___ to share his toys because he wanted to keep them all.", "reluctant",
     ["reluctant", "eager", "proud"]),
    ("The ___ puppy wagged its tail and licked everyone's face.", "friendly",
     ["friendly", "fierce", "sleepy"]),
    ("After the storm, the streets were ___ with fallen branches.", "littered",
     ["littered", "sleepy", "hungry"]),
    ("The instructions were ___, so everyone understood what to do.", "clear",
     ["clear", "confusing", "missing"]),
    ("She showed great ___ by standing up to the bully.", "courage",
     ["courage", "cowardice", "laziness"]),
    ("The library was so ___ you could hear a pin drop.", "quiet",
     ["quiet", "noisy", "loud"]),
    ("His ___ answer showed he had studied hard for the test.", "correct",
     ["correct", "wrong", "funny"]),
]

def _gen_context_clues(age: int) -> dict:
    sentence, correct, opts = random.choice(_CONTEXT_CLUES)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="context_clues",
        expression=sentence,
        prompt_text="Which word fits best?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_HOMOPHONES = [
    ("I went ___ the store.", "to", ["to", "too", "two"]),
    ("___ going to be late!", "They're", ["They're", "Their", "There"]),
    ("The dog wagged ___ tail.", "its", ["its", "it's", "is"]),
    ("___ is a book on the table.", "There", ["There", "Their", "They're"]),
    ("I have ___ apples.", "two", ["two", "to", "too"]),
    ("That's ___ backpack.", "your", ["your", "you're", "yore"]),
    ("___ coming to the party.", "You're", ["You're", "Your", "Yore"]),
    ("The cat licked ___ paws.", "its", ["its", "it's", "is"]),
    ("I ate ___ much cake.", "too", ["too", "to", "two"]),
    ("___ house is very big.", "Their", ["Their", "There", "They're"]),
    ("Can you ___ the bell ringing?", "hear", ["hear", "here", "hare"]),
    ("Come over ___!", "here", ["here", "hear", "hare"]),
    ("The ___ is shining brightly.", "sun", ["sun", "son", "sung"]),
    ("She ___ the answer to the question.", "knew", ["knew", "new", "know"]),
    ("I bought a ___ pair of shoes.", "new", ["new", "knew", "no"]),
    ("The knight rode a white ___.", "horse", ["horse", "hoarse", "house"]),
]

def _gen_homophone_pick(age: int) -> dict:
    sentence, correct, opts = random.choice(_HOMOPHONES)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="homophone_pick",
        expression=sentence,
        prompt_text="Pick the right word!",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_SYNONYMS = [
    ("happy", "joyful", ["joyful", "angry", "tired"]),
    ("big", "enormous", ["enormous", "tiny", "slow"]),
    ("fast", "quick", ["quick", "slow", "heavy"]),
    ("smart", "intelligent", ["intelligent", "silly", "weak"]),
    ("scared", "frightened", ["frightened", "brave", "calm"]),
    ("angry", "furious", ["furious", "peaceful", "sleepy"]),
    ("pretty", "beautiful", ["beautiful", "ugly", "boring"]),
    ("begin", "start", ["start", "finish", "pause"]),
    ("fix", "repair", ["repair", "break", "ignore"]),
    ("difficult", "challenging", ["challenging", "simple", "quick"]),
    ("strange", "peculiar", ["peculiar", "normal", "plain"]),
    ("destroy", "demolish", ["demolish", "build", "save"]),
    ("ancient", "old", ["old", "modern", "fresh"]),
    ("wealthy", "rich", ["rich", "poor", "sad"]),
    ("brave", "courageous", ["courageous", "scared", "lazy"]),
    ("silent", "quiet", ["quiet", "loud", "bright"]),
]

def _gen_synonym_match(age: int) -> dict:
    word, correct, opts = random.choice(_SYNONYMS)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="synonym_match",
        expression=f"🔄 {word}",
        prompt_text=f"Which word means the SAME as '{word}'?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_PREFIX_SUFFIX_HARD = [
    ("care + ful", "careful", "full of care"),
    ("hope + less", "hopeless", "without hope"),
    ("enjoy + ment", "enjoyment", "the state of enjoying"),
    ("dark + ness", "darkness", "the state of being dark"),
    ("wonder + ful", "wonderful", "full of wonder"),
    ("help + less", "helpless", "without help"),
    ("excite + ment", "excitement", "the state of being excited"),
    ("sad + ness", "sadness", "the state of being sad"),
    ("thank + ful", "thankful", "full of thanks"),
    ("power + less", "powerless", "without power"),
    ("amaze + ment", "amazement", "the state of being amazed"),
    ("kind + ness", "kindness", "the state of being kind"),
    ("peace + ful", "peaceful", "full of peace"),
    ("use + less", "useless", "without use"),
    ("over + look", "overlook", "to look past / miss"),
    ("out + run", "outrun", "to run faster than"),
]

def _gen_prefix_suffix_hard(age: int) -> dict:
    parts, combined, meaning = random.choice(_PREFIX_SUFFIX_HARD)
    correct = combined
    others = [c for p, c, m in _PREFIX_SUFFIX_HARD if c != combined]
    random.shuffle(others)
    distractors = others[:2]
    options = [correct] + distractors
    random.shuffle(options)
    return _build(
        mode="prefix_suffix_hard",
        expression=parts,
        prompt_text=f"Put them together! ({meaning})",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


_SENTENCE_COMPLETE = [
    ("The cat sat ___ the mat.", "on", ["on", "of", "into"]),
    ("She is ___ than her brother.", "taller", ["taller", "tallest", "tall"]),
    ("We ___ to the park yesterday.", "went", ["went", "go", "going"]),
    ("This is the ___ movie I've ever seen!", "best", ["best", "better", "good"]),
    ("He ___ his homework before dinner.", "finished", ["finished", "finishing", "finish"]),
    ("The children were ___ in the garden.", "playing", ["playing", "played", "plays"]),
    ("I have ___ seen that movie before.", "never", ["never", "ever", "always"]),
    ("She sings ___ beautifully than anyone.", "more", ["more", "most", "much"]),
    ("They ___ been waiting for an hour.", "have", ["have", "has", "having"]),
    ("The book ___ written by a famous author.", "was", ["was", "were", "be"]),
    ("We need to leave ___ we'll be late.", "or", ["or", "because", "if"]),
    ("She ran fast, ___ she still missed the bus.", "but", ["but", "because", "so"]),
]

def _gen_sentence_complete(age: int) -> dict:
    sentence, correct, opts = random.choice(_SENTENCE_COMPLETE)
    options = list(opts)
    random.shuffle(options)
    return _build(
        mode="sentence_complete",
        expression=sentence,
        prompt_text="Which word completes the sentence?",
        prompt_image=None,
        correct_answer=correct,
        options=options,
    )


# ── Helpers ──

def _make_misspellings(word: str, count: int) -> list[str]:
    """Generate plausible misspellings of a word."""
    misspellings = set()
    attempts = 0
    while len(misspellings) < count and attempts < 100:  # short words hit real ones often
        attempts += 1
        w = list(word)
        if len(w) < 2:
            # Very short word — just swap a letter
            w[0] = random.choice("abcdefghijklmnopqrstuvwxyz")
            mis = "".join(w)
        else:
            op = random.choice(["swap", "replace", "double", "drop"])
            if op == "swap" and len(w) >= 2:
                i = random.randint(0, len(w) - 2)
                w[i], w[i + 1] = w[i + 1], w[i]
            elif op == "replace":
                i = random.randint(0, len(w) - 1)
                vowels = "aeiou"
                consonants = "bcdfghjklmnpqrstvwxyz"
                if w[i] in vowels:
                    w[i] = random.choice([v for v in vowels if v != w[i]])
                else:
                    w[i] = random.choice([c for c in consonants if c != w[i]])
            elif op == "double" and len(w) >= 3:
                i = random.randint(1, len(w) - 1)
                w.insert(i, w[i])
            elif op == "drop" and len(w) >= 3:
                i = random.randint(1, len(w) - 1)
                w.pop(i)
            mis = "".join(w)
        if mis != word and mis not in misspellings and mis not in _REAL_WORDS:
            misspellings.add(mis)
    # Fallback if we can't generate enough
    for suffix in ("e", "s", "ee", "ss", word[-1]):
        if len(misspellings) >= count:
            break
        if word + suffix not in _REAL_WORDS:
            misspellings.add(word + suffix)
    return list(misspellings)[:count]


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
    # Young kids (age <= 5)
    "letter_sound": _gen_letter_sound,
    "beginning_sound": _gen_beginning_sound,
    "rhyme_match": _gen_rhyme_match,
    "cvc_blend": _gen_cvc_blend,
    # Grade 2 (age 6-7)
    "sight_word_spell": _gen_sight_word_spell,
    "vocabulary_match": _gen_vocabulary_match,
    "antonym_match": _gen_antonym_match,
    "prefix_suffix": _gen_prefix_suffix,
    # Grade 3-4 (age >= 8)
    "vocabulary_hard": _gen_vocabulary_hard,
    "context_clues": _gen_context_clues,
    "homophone_pick": _gen_homophone_pick,
    "synonym_match": _gen_synonym_match,
    "prefix_suffix_hard": _gen_prefix_suffix_hard,
    "sentence_complete": _gen_sentence_complete,
    # Grammar / word structure
    "plural_form": _gen_plural_form,
    "past_tense": _gen_past_tense,
    "syllable_count": _gen_syllable_count,
}


def generate_english_question(mode: str, age: int) -> dict:
    """Generate a single question in a named mode. See math_generator's twin."""
    generator = _GENERATORS.get(mode)
    if generator is None:
        raise ValueError(f"Unknown English question mode: {mode}")
    return generator(age)


def available_modes() -> set[str]:
    return set(_GENERATORS)
