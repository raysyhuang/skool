from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.progress import UserCharacterProgress


def update_mastery(db: Session, user_id: int, character_id: int, is_correct: bool) -> UserCharacterProgress:
    """Update mastery score for a user-character pair. +1 correct, -1 wrong, clamped 0-5."""
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
        )
        db.add(progress)

    if is_correct:
        progress.mastery_score = min(5, progress.mastery_score + 1)
        progress.correct_count += 1
    else:
        progress.mastery_score = max(0, progress.mastery_score - 1)
        progress.wrong_count += 1

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
