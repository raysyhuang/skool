from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, date as dt_date

from app.database import Base


class DailyQuest(Base):
    """Daily quest definitions."""
    __tablename__ = "daily_quests"
    
    id = Column(Integer, primary_key=True, index=True)
    quest_type = Column(String, nullable=False)  # "play_session", "perfect_session", "streak", etc.
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    target_value = Column(Integer, default=1)
    reward_type = Column(String, default="stars")  # "stars", "coins", "points"
    reward_amount = Column(Integer, default=5)
    icon = Column(String, nullable=True)  # emoji or icon identifier


class UserDailyQuestProgress(Base):
    """Tracks per-user progress on daily quests."""
    __tablename__ = "user_daily_quest_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quest_id = Column(Integer, ForeignKey("daily_quests.id"), nullable=False)
    date = Column(Date, default=dt_date.today, nullable=False, index=True)
    current_value = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    claimed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User")
    quest = relationship("DailyQuest")
