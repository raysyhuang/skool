from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, timezone

from app.models.progress import UserCharacterProgress


def _quality_from_attempt(is_correct: bool, is_first_attempt: bool) -> int:
    """Map answer result to SM-2 quality score (0-5).

    - correct on 1st attempt → q=5 (perfect recall)
    - correct on retry        → q=3 (correct but hesitant)
    - wrong (final)           → q=1 (complete failure)
    """
    if is_correct:
        return 5 if is_first_attempt else 3
    return 1


def _mastery_from_repetitions(repetitions: int) -> int:
    """Map SM-2 repetitions to display mastery score (0-5).

    Keeps backward compatibility with car evolution, achievements, etc.
    """
    if repetitions <= 0:
        return 0
    elif repetitions == 1:
        return 1
    elif repetitions == 2:
        return 2
    elif repetitions <= 4:
        return 3
    elif repetitions <= 6:
        return 4
    else:
        return 5


def update_mastery(
    db: Session,
    user_id: int,
    character_id: int,
    is_correct: bool,
    is_first_attempt: bool = True,
) -> UserCharacterProgress:
    """Update SM-2 spaced repetition data for a user-character pair.

    Implements the SM-2 algorithm:
    - Correct answers increase interval and repetitions
    - Wrong answers reset repetitions and schedule immediate review
    - Easiness factor adjusts based on response quality
    """
    progress = (
        db.query(UserCharacterProgress)
        .filter_by(user_id=user_id, character_id=character_id)
        .first()
    )

    if not progress:
        progress = UserCharacterProgress(
            user_id=user_id,
            character_id=character_id,
            mastery_score=0,
            correct_count=0,
            wrong_count=0,
            easiness_factor=2.5,
            sm2_interval=0,
            sm2_repetitions=0,
            next_review_date=None,
        )
        db.add(progress)

    quality = _quality_from_attempt(is_correct, is_first_attempt)
    today = date.today()

    # Track counts
    if is_correct:
        progress.correct_count += 1
    else:
        progress.wrong_count += 1

    # SM-2 core algorithm
    if quality >= 3:  # correct
        if progress.sm2_repetitions == 0:
            interval = 1
        elif progress.sm2_repetitions == 1:
            interval = 3
        else:
            interval = round(progress.sm2_interval * progress.easiness_factor)
        progress.sm2_repetitions += 1
        progress.sm2_interval = max(interval, 1)
    else:  # wrong
        progress.sm2_repetitions = 0
        progress.sm2_interval = 0  # review again today

    # Update easiness factor (EF)
    ef = progress.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    progress.easiness_factor = max(1.3, ef)

    # Schedule next review
    progress.next_review_date = today + timedelta(days=progress.sm2_interval)

    # Update display mastery for backward compatibility
    progress.mastery_score = _mastery_from_repetitions(progress.sm2_repetitions)

    progress.last_seen = datetime.now(timezone.utc)
    db.flush()
    return progress


def get_mastery(db: Session, user_id: int, character_id: int) -> int:
    """Get current mastery score for a user-character pair."""
    progress = (
        db.query(UserCharacterProgress)
        .filter_by(user_id=user_id, character_id=character_id)
        .first()
    )
    return progress.mastery_score if progress else 0
