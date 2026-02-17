from sqlalchemy.orm import Session

from app.models.user import User


def get_user(db: Session, user_id: int) -> User | None:
    """Look up a child user by ID."""
    return db.query(User).filter(User.id == user_id, User.role == "child").first()


def get_child_users(db: Session) -> list[User]:
    """Return all child users for login screen."""
    return db.query(User).filter(User.role == "child").all()
