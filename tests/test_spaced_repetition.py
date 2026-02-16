from app.services.spaced_repetition import update_mastery, get_mastery


def test_initial_mastery_is_zero(db, sample_user, sample_characters):
    char = sample_characters[0]
    assert get_mastery(db, sample_user.id, char.id) == 0


def test_correct_answer_increases_mastery(db, sample_user, sample_characters):
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert get_mastery(db, sample_user.id, char.id) == 1


def test_wrong_answer_decreases_mastery(db, sample_user, sample_characters):
    char = sample_characters[0]
    # First increase to 2
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert get_mastery(db, sample_user.id, char.id) == 2
    # Now decrease
    update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert get_mastery(db, sample_user.id, char.id) == 1


def test_mastery_clamped_at_zero(db, sample_user, sample_characters):
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert get_mastery(db, sample_user.id, char.id) == 0
    update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert get_mastery(db, sample_user.id, char.id) == 0


def test_mastery_clamped_at_five(db, sample_user, sample_characters):
    char = sample_characters[0]
    for _ in range(10):
        update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert get_mastery(db, sample_user.id, char.id) == 5


def test_correct_count_tracked(db, sample_user, sample_characters):
    char = sample_characters[0]
    progress = update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert progress.correct_count == 1
    progress = update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert progress.correct_count == 2


def test_wrong_count_tracked(db, sample_user, sample_characters):
    char = sample_characters[0]
    progress = update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert progress.wrong_count == 1
