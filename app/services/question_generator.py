import json
import random
from sqlalchemy.orm import Session

from app.models.character import Character
from app.models.progress import UserCharacterProgress
from app.config import get_settings


# Question modes:
#   "char_to_image"   — show character, pick correct image   (default for son)
#   "image_to_char"   — show image, pick correct character
#   "char_to_meaning" — show character, pick correct English  (default for daughter)
#   "meaning_to_char" — show English word, pick correct character
#   "fill_in_blank"   — show compound word with one char blanked, pick missing char
#   "pinyin_to_char"  — show pinyin, pick correct character
#   "audio_to_char"   — listen to audio, pick correct character
QUESTION_MODES = [
    "char_to_image", "image_to_char", "char_to_meaning", "meaning_to_char",
    "fill_in_blank", "pinyin_to_char", "audio_to_char",
]

# Confusable groups: meanings whose icons look too similar for a 4-year-old.
# Distractors are never drawn from the same group as the correct answer.
_CONFUSABLE_GROUPS: list[set[str]] = [
    {"red", "blue", "green", "yellow", "white", "black", "pink", "orange"},
    {"up", "down", "left", "right"},
    {"run", "walk", "jump", "swim"},
    {"eat", "drink"},
    {"happy", "sad", "cry", "laugh", "love"},
    {"person", "dad", "mom", "baby", "friend", "teacher", "brother", "sister", "grandpa", "grandma"},
    {"big", "small", "long", "short"},
    {"fast", "slow"},
    {"hot", "cold"},
    {"rice", "cooked rice", "noodles", "beef noodle soup", "soup"},
    {"dumplings", "steamed bun"},
    {"water", "rain", "sea/ocean", "river"},
    {"ball", "soccer", "basketball"},
    {"cat", "dog"},
    {"bird", "chicken", "penguin", "parrot"},
    {"write", "read"},
    {"bowl", "cup", "tea", "juice", "milk", "cola"},
    {"bed", "table", "chair"},
    {"car", "bus", "train", "bike", "subway"},
    {"bug", "ant", "bee", "butterfly"},
    {"horse", "cow", "sheep", "pig", "elephant", "bear", "tiger"},
    {"fish", "frog", "dolphin", "whale", "turtle", "shrimp"},
    {"chopsticks", "spoon"},
    {"sit", "stand"},
    {"sing", "dance"},
    {"house", "school", "hospital", "restaurant", "supermarket"},
]

# Build a reverse lookup: meaning → set of confusable meanings
_CONFUSABLE_LOOKUP: dict[str, set[str]] = {}
for _group in _CONFUSABLE_GROUPS:
    for _meaning in _group:
        _CONFUSABLE_LOOKUP[_meaning] = _group


def _exclude_confusable(correct_char: Character, candidates: list[Character]) -> list[Character]:
    """Filter out candidates whose meaning is in the same confusable group as correct_char."""
    group = _CONFUSABLE_LOOKUP.get(correct_char.meaning)
    if not group:
        return candidates
    return [c for c in candidates if c.meaning not in group]


def select_characters(db: Session, user_id: int, count: int = 5, theme: str = "racing") -> list[Character]:
    """Select characters weighted by inverse mastery. Low mastery = high frequency."""
    # Get all characters available for this user
    target_filter = ["son", "all"] if theme == "racing" else ["daughter", "all"]
    query = db.query(Character).filter(Character.target_users.in_(target_filter))
    # For young kids (racing/son), only pick characters with images — all modes are picture-based
    if theme == "racing":
        query = query.filter(Character.image_url.isnot(None))
    characters = query.all()

    if not characters:
        return []

    # Get progress for weighting
    progress_map = {}
    progress_records = (
        db.query(UserCharacterProgress)
        .filter_by(user_id=user_id)
        .all()
    )
    for p in progress_records:
        progress_map[p.character_id] = p.mastery_score

    # Weight: unseen chars get weight 6, mastery 0 gets 6, mastery 5 gets 1
    weighted = []
    for char in characters:
        mastery = progress_map.get(char.id, -1)
        if mastery == -1:
            weight = 6  # Never seen — highest priority
        else:
            weight = 6 - mastery  # mastery 0->6, mastery 5->1
        weighted.append((char, max(weight, 1)))

    # Weighted random selection without replacement
    selected = []
    pool = list(weighted)
    for _ in range(min(count, len(pool))):
        total = sum(w for _, w in pool)
        r = random.uniform(0, total)
        cumulative = 0
        for i, (char, w) in enumerate(pool):
            cumulative += w
            if r <= cumulative:
                selected.append(char)
                pool.pop(i)
                break

    return selected


def pick_question_mode(theme: str, char: Character) -> str:
    """Pick a random question mode based on theme and character capabilities."""
    has_image = bool(char.image_url)
    is_compound = len(char.character) >= 2

    if theme == "racing":
        # Son (age 4): picture-only, simple matching — no reading or true/false
        candidates = []
        if has_image:
            candidates += ["char_to_image"] * 100  # show character, pick picture
    else:
        # Daughter (age 8): weighted mode distribution
        candidates = []
        candidates += ["char_to_meaning"] * 25
        candidates += ["meaning_to_char"] * 20
        if is_compound:
            candidates += ["fill_in_blank"] * 20
        candidates += ["audio_to_char"] * 20
        candidates += ["pinyin_to_char"] * 15

    if not candidates:
        # Fallback
        return "char_to_meaning"

    return random.choice(candidates)


def generate_options(db: Session, correct_char: Character, count: int = 2) -> list[str]:
    """Generate distractor options + correct answer, shuffled. Returns list of meanings."""
    all_chars = (
        db.query(Character)
        .filter(Character.id != correct_char.id)
        .all()
    )

    # Pick distractors from different meanings
    distractors = random.sample(all_chars, min(count, len(all_chars)))
    options = [correct_char.meaning] + [d.meaning for d in distractors]
    random.shuffle(options)
    return options


def generate_image_options(db: Session, correct_char: Character, count: int = 2) -> list[str]:
    """Generate picture-based distractor options for son's mode. Returns list of image_urls."""
    all_chars = (
        db.query(Character)
        .filter(Character.id != correct_char.id)
        .filter(Character.image_url.isnot(None))
        .all()
    )

    # Exclude visually confusable icons from distractors
    filtered = _exclude_confusable(correct_char, all_chars)
    # Fall back to unfiltered pool if not enough candidates remain
    pool = filtered if len(filtered) >= count else all_chars
    distractors = random.sample(pool, min(count, len(pool)))

    # Use image_url if available, fall back to meaning
    correct_option = correct_char.image_url or correct_char.meaning
    distractor_options = [d.image_url or d.meaning for d in distractors]

    options = [correct_option] + distractor_options
    random.shuffle(options)
    return options


def generate_character_options(db: Session, correct_char: Character, count: int = 2) -> list[str]:
    """Generate character-based distractor options (for reverse modes). Returns list of characters."""
    all_chars = (
        db.query(Character)
        .filter(Character.id != correct_char.id)
        .all()
    )

    distractors = random.sample(all_chars, min(count, len(all_chars)))
    options = [correct_char.character] + [d.character for d in distractors]
    random.shuffle(options)
    return options


def generate_question(db: Session, char: Character, mode: str, count: int = 2) -> dict:
    """Generate a complete question for any mode.

    Returns dict with:
      - mode: the question mode
      - prompt: what to show (character, image_url, or meaning)
      - prompt_type: "character", "image", or "text"
      - correct_answer: the correct option value
      - options: list of option values
      - option_type: "image", "character", or "text"
      (plus extra fields for true_or_false and fill_in_blank)
    """
    if mode == "char_to_image":
        options = generate_image_options(db, char, count)
        return {
            "mode": mode,
            "prompt": char.character,
            "prompt_type": "character",
            "pinyin": char.pinyin,
            "correct_answer": char.image_url or char.meaning,
            "options": options,
            "option_type": "image",
        }
    elif mode == "image_to_char":
        options = generate_character_options(db, char, count)
        return {
            "mode": mode,
            "prompt": char.image_url or char.meaning,
            "prompt_type": "image",
            "pinyin": char.pinyin,
            "correct_answer": char.character,
            "options": options,
            "option_type": "character",
        }
    elif mode == "char_to_meaning":
        options = generate_options(db, char, count)
        return {
            "mode": mode,
            "prompt": char.character,
            "prompt_type": "character",
            "pinyin": char.pinyin,
            "correct_answer": char.meaning,
            "options": options,
            "option_type": "text",
        }
    elif mode == "meaning_to_char":
        options = generate_character_options(db, char, count)
        return {
            "mode": mode,
            "prompt": char.meaning,
            "prompt_type": "text",
            "pinyin": char.pinyin,
            "correct_answer": char.character,
            "options": options,
            "option_type": "character",
        }
    elif mode == "audio_to_char":
        options = generate_character_options(db, char, count)
        return {
            "mode": mode,
            "prompt": char.character,
            "prompt_type": "audio",
            "pinyin": char.pinyin,
            "correct_answer": char.character,
            "options": options,
            "option_type": "character",
        }
    elif mode == "fill_in_blank":
        return _generate_fill_in_blank(db, char, count)
    elif mode == "pinyin_to_char":
        options = generate_character_options(db, char, count)
        return {
            "mode": mode,
            "prompt": char.pinyin,
            "prompt_type": "pinyin",
            "pinyin": char.pinyin,
            "correct_answer": char.character,
            "options": options,
            "option_type": "character",
        }
    else:
        raise ValueError(f"Unknown question mode: {mode}")


def _generate_fill_in_blank(db: Session, char: Character, count: int = 2) -> dict:
    """Generate a fill-in-the-blank question for compound words."""
    word = char.character
    if len(word) < 2:
        # Fallback to char_to_meaning for single chars
        return generate_question(db, char, "char_to_meaning", count)

    # Pick a random position to blank out
    blank_pos = random.randint(0, len(word) - 1)
    blank_char = word[blank_pos]
    display_word = word[:blank_pos] + "___" + word[blank_pos + 1:]

    # Generate distractor characters (single chars only)
    all_chars = (
        db.query(Character)
        .filter(Character.id != char.id)
        .all()
    )

    # Collect unique single characters for distractors
    distractor_pool = set()
    for c in all_chars:
        for ch in c.character:
            if ch != blank_char:
                distractor_pool.add(ch)

    distractor_list = list(distractor_pool)
    distractors = random.sample(distractor_list, min(count, len(distractor_list)))
    options = [blank_char] + distractors
    random.shuffle(options)

    # Encode display_word and meaning_hint as trailing elements for DB storage
    options_with_meta = options + [display_word, char.meaning]

    return {
        "mode": "fill_in_blank",
        "prompt": display_word,
        "prompt_type": "fill_blank",
        "pinyin": char.pinyin,
        "full_word": word,
        "blank_char": blank_char,
        "blank_position": blank_pos,
        "meaning_hint": char.meaning,
        "correct_answer": blank_char,
        "options": options_with_meta,
        "option_type": "character",
    }
