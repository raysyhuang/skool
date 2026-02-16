from sqlalchemy.orm import Session

from app.models.user import User


def validate_pin(db: Session, user_id: int, pin: str) -> User | None:
    """Validate a user's PIN. Returns the User if valid, None otherwise."""
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.pin == pin:
        return user
    return None


def get_child_users(db: Session) -> list[User]:
    """Return all child users for login screen."""
    return db.query(User).filter(User.role == "child").all()
