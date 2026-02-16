from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    change = Column(Integer, nullable=False)        # +2 for correct, +5 for daily bonus, etc.
    reason = Column(String, nullable=False)          # "correct_answer", "daily_bonus", "streak_bonus"
    balance_after = Column(Integer, nullable=False)  # running total for audit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="ledger_entries")
