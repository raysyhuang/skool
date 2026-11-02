from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_type = Column(String, nullable=False, default="chinese")  # "chinese", "math", "logic"
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    total_correct = Column(Integer, default=0)
    total_wrong = Column(Integer, default=0)
    points_earned = Column(Integer, default=0)
    
    # Combo tracking
    current_combo = Column(Integer, default=0)
    max_combo = Column(Integer, default=0)
    combo_bonus = Column(Integer, default=0)

    user = relationship("User", back_populates="sessions")
    questions = relationship("SessionQuestion", back_populates="session", order_by="SessionQuestion.question_number")


class SessionQuestion(Base):
    __tablename__ = "session_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)  # null for math/logic
    topic_id = Column(Integer, ForeignKey("learning_topics.id"), nullable=True)  # taxonomy topic for math/english
    question_number = Column(Integer, nullable=False)  # 1-5
    question_mode = Column(String, default="char_to_image")  # char_to_image, image_to_char, char_to_meaning, meaning_to_char, math_*, logic_*
    correct_answer = Column(String, nullable=False)     # the correct image_url, meaning, or character
    options = Column(String, nullable=False)             # JSON list of 3 options
    prompt_data = Column(String, nullable=True)          # JSON blob for math/logic question details
    selected_answer = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    answered_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)  # for speed bonus tracking
    first_try = Column(Boolean, default=True)  # False if hint was used
    # Right on the first attempt. is_correct flips to True after a retry, so
    # scoring and the parent dashboard read this instead.
    first_attempt_correct = Column(Boolean, nullable=True)
    first_selected_answer = Column(String, nullable=True)  # selected_answer is overwritten by a retry
    hint_shown = Column(Boolean, default=False)

    session = relationship("GameSession", back_populates="questions")
    character = relationship("Character")
    topic = relationship("LearningTopic")
