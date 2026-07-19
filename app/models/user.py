from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from datetime import date

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    pin = Column(String(4), nullable=False)
    age = Column(Integer, nullable=True)
    theme = Column(String, nullable=False, default="racing")  # "racing" or "pony"
    role = Column(String, nullable=False, default="child")     # "child" or "parent"

    # Denormalized balances for instant reads
    points = Column(Integer, default=0)
    stars = Column(Integer, default=0)
    coins = Column(Integer, default=0)

    # Daily tracking
    streak = Column(Integer, default=0)
    sessions_today = Column(Integer, default=0)
    last_played_date = Column(Date, nullable=True)

    # Gamification extras
    streak_freezes = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    perfect_sessions = Column(Integer, default=0)
    total_sessions_completed = Column(Integer, default=0)
    car_level = Column(Integer, default=0)

    # Store / customization
    equipped_car_skin = Column(String, nullable=True)
    equipped_background = Column(String, nullable=True)
    equipped_trail = Column(String, nullable=True)

    # Relationships
    progress = relationship("UserCharacterProgress", back_populates="user")
    sessions = relationship("GameSession", back_populates="user")
    ledger_entries = relationship("PointsLedger", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    inventory = relationship("UserInventory", back_populates="user")
    quest_progress = relationship("QuestProgress", back_populates="user")

    def reset_daily_if_needed(self):
        """Reset sessions_today when the day changes.

        Safe to call from any handler; streak logic lives in
        record_play_today(), which only create_session invokes.
        """
        if self.last_played_date != date.today():
            self.sessions_today = 0

    def record_play_today(self):
        """Stamp today's play and update the streak. Idempotent within a day."""
        today = date.today()
        if self.last_played_date == today:
            return
        if self.last_played_date is None:
            self.streak = 1
        elif (today - self.last_played_date).days == 1:
            self.streak += 1
        else:
            # Missed a day: one freeze preserves the streak, otherwise restart
            if self.streak_freezes > 0:
                self.streak_freezes -= 1
            else:
                self.streak = 1
        if self.streak > self.best_streak:
            self.best_streak = self.streak
        self.sessions_today = 0
        self.last_played_date = today
