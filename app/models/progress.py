from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class UserCharacterProgress(Base):
    __tablename__ = "user_character_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    mastery_score = Column(Integer, default=0)  # 0-5, kept for display/backward compat
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    last_seen = Column(DateTime, nullable=True)

    # SM-2 fields
    easiness_factor = Column(Float, default=2.5)       # EF, min 1.3
    sm2_interval = Column(Integer, default=0)           # days until next review
    sm2_repetitions = Column(Integer, default=0)        # consecutive correct count
    next_review_date = Column(Date, nullable=True)      # when to next show this character

    user = relationship("User", back_populates="progress")
    character = relationship("Character", back_populates="progress")
