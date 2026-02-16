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

    # Relationships
    progress = relationship("UserCharacterProgress", back_populates="user")
    sessions = relationship("GameSession", back_populates="user")
    ledger_entries = relationship("PointsLedger", back_populates="user")

    def reset_daily_if_needed(self):
        """Reset sessions_today if it's a new day. Update streak."""
        today = date.today()
        if self.last_played_date != today:
            if self.last_played_date and (today - self.last_played_date).days == 1:
                self.streak += 1
            elif self.last_played_date and (today - self.last_played_date).days > 1:
                self.streak = 0
            self.sessions_today = 0
