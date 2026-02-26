"""Achievement badge system.

Badge definitions are stored here as a dict (not in DB).
check_badges() is called after complete_session() and returns newly earned badges.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.achievement import UserAchievement
from app.models.session import GameSession


# Badge definitions: key -> { name, description, emoji }
BADGES = {
    "first_session": {
        "name": "First Race",
        "description": "Complete your first session",
        "emoji": "\U0001F3C1",  # chequered flag
    },
    "perfect_5": {
        "name": "Perfect Score",
        "description": "Get 5/5 on a session",
        "emoji": "\U0001F31F",  # glowing star
    },
    "streak_3": {
        "name": "On Fire",
        "description": "3-day streak",
        "emoji": "\U0001F525",  # fire
    },
    "streak_7": {
        "name": "Week Warrior",
        "description": "7-day streak",
        "emoji": "\U0001F4AA",  # flexed bicep
    },
    "streak_14": {
        "name": "Unstoppable",
        "description": "14-day streak",
        "emoji": "\U0001F3C6",  # trophy
    },
    "math_whiz": {
        "name": "Math Whiz",
        "description": "Complete 10 math sessions",
        "emoji": "\U0001F9EE",  # abacus
    },
    "bookworm": {
        "name": "Bookworm",
        "description": "Complete 10 Chinese sessions",
        "emoji": "\U0001F4DA",  # books
    },
    "polyglot": {
        "name": "Polyglot",
        "description": "Complete 10 English sessions",
        "emoji": "\U0001F30D",  # globe
    },
    "century": {
        "name": "Century Club",
        "description": "Earn 100 stars",
        "emoji": "\U00002B50",  # star
    },
    "collector_5": {
        "name": "Car Collector",
        "description": "Reach car level 2 (Sedan)",
        "emoji": "\U0001F697",  # car
    },
    "collector_15": {
        "name": "Speed Demon Garage",
        "description": "Reach car level 3 (Sports Car)",
        "emoji": "\U0001F3CE\uFE0F",  # racing car
    },
    "speed_demon": {
        "name": "Speed Demon",
        "description": "Answer 5 questions in under 3 seconds each",
        "emoji": "\u26A1",  # lightning
    },
}


def get_earned_badges(db: Session, user_id: int) -> set[str]:
    """Return the set of badge keys already earned by this user."""
    rows = db.query(UserAchievement.badge_key).filter_by(user_id=user_id).all()
    return {r[0] for r in rows}


def _award_badge(db: Session, user_id: int, badge_key: str) -> UserAchievement:
    ua = UserAchievement(
        user_id=user_id,
        badge_key=badge_key,
        earned_at=datetime.now(timezone.utc),
    )
    db.add(ua)
    return ua


def check_badges(db: Session, user: User, session_result: dict, game_session: GameSession) -> list[dict]:
    """Check all badge conditions and award any newly earned badges.

    Returns list of newly earned badge dicts: [{ key, name, emoji, description }]
    """
    earned = get_earned_badges(db, user.id)
    newly_earned = []

    def _try_award(key: str):
        if key not in earned:
            _award_badge(db, user.id, key)
            badge = BADGES[key]
            newly_earned.append({
                "key": key,
                "name": badge["name"],
                "emoji": badge["emoji"],
                "description": badge["description"],
            })

    # first_session
    if user.total_sessions_completed >= 1:
        _try_award("first_session")

    # perfect_5
    if session_result.get("total_correct", 0) == len(game_session.questions):
        _try_award("perfect_5")

    # streak milestones
    if user.streak >= 3:
        _try_award("streak_3")
    if user.streak >= 7:
        _try_award("streak_7")
    if user.streak >= 14:
        _try_award("streak_14")

    # Game type counts
    game_type = game_session.game_type
    completed_of_type = (
        db.query(GameSession)
        .filter_by(user_id=user.id, game_type=game_type)
        .filter(GameSession.completed_at.isnot(None))
        .count()
    )

    if game_type == "math" and completed_of_type >= 10:
        _try_award("math_whiz")
    if game_type == "chinese" and completed_of_type >= 10:
        _try_award("bookworm")
    if game_type == "english" and completed_of_type >= 10:
        _try_award("polyglot")

    # century (100 stars total earned, approximate via points)
    if user.points >= 100:
        _try_award("century")

    # car collector milestones
    if user.car_level >= 1:
        _try_award("collector_5")
    if user.car_level >= 2:
        _try_award("collector_15")

    # speed_demon: all 5 questions answered in under 3 seconds each
    fast_count = 0
    for q in game_session.questions:
        if q.started_at and q.answered_at:
            delta = (q.answered_at - q.started_at).total_seconds()
            if delta < 3.0:
                fast_count += 1
    if fast_count == len(game_session.questions):
        _try_award("speed_demon")

    return newly_earned
