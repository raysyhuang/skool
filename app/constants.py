"""Shared constants used across the application."""


class QuestionMode:
    """Valid question mode strings for Chinese character games."""
    CHAR_TO_IMAGE = "char_to_image"
    IMAGE_TO_CHAR = "image_to_char"
    CHAR_TO_MEANING = "char_to_meaning"
    MEANING_TO_CHAR = "meaning_to_char"
    PINYIN_TO_CHAR = "pinyin_to_char"
    TRUE_OR_FALSE = "true_or_false"
    FILL_IN_BLANK = "fill_in_blank"


class MathMode:
    """Valid question mode strings for math games."""
    ADDITION_SIMPLE = "addition_simple"
    ADDITION_WITH_CARRYING = "addition_with_carrying"
    SUBTRACTION_SIMPLE = "subtraction_simple"
    SUBTRACTION_WITH_BORROWING = "subtraction_with_borrowing"
    MULTIPLICATION_SIMPLE = "multiplication_simple"
    MULTIPLICATION_TABLES = "multiplication_tables"
    DIVISION_SIMPLE = "division_simple"
    COMPARISON = "comparison"
    NUMBER_LINE = "number_line"
    WORD_PROBLEM = "word_problem"
    SHAPE_RECOGNITION = "shape_recognition"
    COUNTING = "counting"
    PLACE_VALUE = "place_value"


class LogicMode:
    """Valid question mode strings for logic games."""
    PATTERN = "pattern"
    SEQUENCE = "sequence"
    SHAPE_PATTERN = "shape_pattern"
    COLOR_PATTERN = "color_pattern"
    SIZE_PATTERN = "size_pattern"
    ODD_ONE_OUT = "odd_one_out"
    MATCHING = "matching"


class EnglishMode:
    """Valid question mode strings for English games."""
    WORD_TO_IMAGE = "word_to_image"
    IMAGE_TO_WORD = "image_to_word"
    FILL_IN_BLANK = "fill_in_blank"
    RHYMING = "rhyming"
    PLURALS = "plurals"
    VERB_TENSE = "verb_tense"
    OPPOSITES = "opposites"
    SYNONYMS = "synonyms"
