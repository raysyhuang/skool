from datetime import date, timedelta

from app.services.spaced_repetition import update_mastery, get_mastery
from app.models.progress import UserCharacterProgress


def test_initial_mastery_is_zero(db, sample_user, sample_characters):
    char = sample_characters[0]
    assert get_mastery(db, sample_user.id, char.id) == 0


def test_correct_answer_increases_mastery(db, sample_user, sample_characters):
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert get_mastery(db, sample_user.id, char.id) == 1


def test_wrong_answer_resets_repetitions(db, sample_user, sample_characters):
    char = sample_characters[0]
    # Build up 2 correct
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert get_mastery(db, sample_user.id, char.id) == 2
    # Wrong resets
    update_mastery(db, sample_user.id, char.id, is_correct=False)
    prog = db.query(UserCharacterProgress).filter_by(
        user_id=sample_user.id, character_id=char.id
    ).first()
    assert prog.sm2_repetitions == 0
    assert prog.sm2_interval == 0
    assert prog.mastery_score == 0


def test_mastery_clamped_at_zero(db, sample_user, sample_characters):
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert get_mastery(db, sample_user.id, char.id) == 0
    update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert get_mastery(db, sample_user.id, char.id) == 0


def test_mastery_reaches_five_with_many_correct(db, sample_user, sample_characters):
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


# ── SM-2 specific tests ──

def test_sm2_first_correct_interval_is_one(db, sample_user, sample_characters):
    """First correct answer should set interval to 1 day."""
    char = sample_characters[0]
    progress = update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert progress.sm2_interval == 1
    assert progress.sm2_repetitions == 1
    assert progress.next_review_date == date.today() + timedelta(days=1)


def test_sm2_second_correct_interval_is_three(db, sample_user, sample_characters):
    """Second consecutive correct answer should set interval to 3 days."""
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    progress = update_mastery(db, sample_user.id, char.id, is_correct=True)
    assert progress.sm2_interval == 3
    assert progress.sm2_repetitions == 2
    assert progress.next_review_date == date.today() + timedelta(days=3)


def test_sm2_intervals_grow_with_ef(db, sample_user, sample_characters):
    """After third correct, interval = round(prev_interval * EF)."""
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=True)   # interval=1
    update_mastery(db, sample_user.id, char.id, is_correct=True)   # interval=3
    progress = update_mastery(db, sample_user.id, char.id, is_correct=True)  # interval=round(3*EF)
    assert progress.sm2_repetitions == 3
    assert progress.sm2_interval == round(3 * progress.easiness_factor)


def test_sm2_wrong_resets_to_today(db, sample_user, sample_characters):
    """Wrong answer resets interval to 0, schedules review today."""
    char = sample_characters[0]
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    update_mastery(db, sample_user.id, char.id, is_correct=True)
    progress = update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert progress.sm2_interval == 0
    assert progress.sm2_repetitions == 0
    assert progress.next_review_date == date.today()


def test_sm2_easiness_factor_never_below_min(db, sample_user, sample_characters):
    """EF should never drop below 1.3 even after many wrong answers."""
    char = sample_characters[0]
    for _ in range(20):
        progress = update_mastery(db, sample_user.id, char.id, is_correct=False)
    assert progress.easiness_factor >= 1.3


def test_sm2_retry_correct_gives_lower_quality(db, sample_user, sample_characters):
    """Retry correct (is_first_attempt=False) uses quality=3 (less EF boost)."""
    char1 = sample_characters[0]
    char2 = sample_characters[1]

    # First attempt correct → quality 5
    p1 = update_mastery(db, sample_user.id, char1.id, is_correct=True, is_first_attempt=True)
    # Retry correct → quality 3
    p2 = update_mastery(db, sample_user.id, char2.id, is_correct=True, is_first_attempt=False)

    # Both should have interval=1 (first correct)
    assert p1.sm2_interval == 1
    assert p2.sm2_interval == 1
    # But quality 5 gives higher EF than quality 3
    assert p1.easiness_factor > p2.easiness_factor
