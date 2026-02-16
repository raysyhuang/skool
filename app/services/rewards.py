from sqlalchemy.orm import Session

from app.models.user import User
from app.models.rewards import PointsLedger
from app.config import get_settings


def award_points(db: Session, user: User, amount: int, reason: str) -> None:
    """Award points to a user and log to ledger."""
    if amount == 0:
        return

    user.points += amount
    user.stars += amount * get_settings().stars_per_point

    # Auto-convert stars to coins
    settings = get_settings()
    if user.stars >= settings.coins_per_stars:
        new_coins = user.stars // settings.coins_per_stars
        user.coins += new_coins
        user.stars = user.stars % settings.coins_per_stars

    entry = PointsLedger(
        user_id=user.id,
        change=amount,
        reason=reason,
        balance_after=user.points,
    )
    db.add(entry)
    db.flush()


def get_conversion_status(user: User) -> dict:
    """Get current reward status and progress toward next conversion."""
    settings = get_settings()
    return {
        "points": user.points,
        "stars": user.stars,
        "coins": user.coins,
        "stars_to_next_coin": settings.coins_per_stars - (user.stars % settings.coins_per_stars),
        "coins_to_next_rmb": settings.rmb_per_coins - (user.coins % settings.rmb_per_coins),
        "rmb_value": (user.coins // settings.rmb_per_coins) * settings.rmb_payout,
    }
