from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class ContentReport(Base):
    """A parent's "this question looks wrong" flag on one asked question.

    The question's text and answers are snapshotted so the report still
    makes sense after the content (or the session) changes.
    """

    __tablename__ = "content_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # the child who saw it
    session_question_id = Column(Integer, ForeignKey("session_questions.id"), nullable=True)
    mode = Column(String, nullable=True)
    prompt = Column(String, nullable=True)  # character / expression / prompt text
    correct_answer = Column(String, nullable=True)
    selected_answer = Column(String, nullable=True)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved = Column(Boolean, default=False, nullable=False)
