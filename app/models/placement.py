"""Placement test models for adaptive difficulty."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class PlacementTest(Base):
    """Records of placement tests for skill level assessment."""
    __tablename__ = "placement_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)  # "math", "english", "chinese"
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    estimated_ability = Column(Float, nullable=True)  # Elo-style rating (1000-2000)
    recommended_grade = Column(String, nullable=True)  # "K", "1", "2", etc.
    
    user = relationship("User")
    responses = relationship("PlacementResponse", back_populates="test")


class PlacementResponse(Base):
    """Individual question responses in a placement test."""
    __tablename__ = "placement_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("placement_tests.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("learning_topics.id"), nullable=True)
    question_number = Column(Integer, nullable=False)
    difficulty = Column(Float, nullable=False)  # Question difficulty (Elo-style)
    correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    test = relationship("PlacementTest", back_populates="responses")
    topic = relationship("LearningTopic")


class SkillAbility(Base):
    """Per-topic ability estimates for adaptive difficulty."""
    __tablename__ = "skill_abilities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("learning_topics.id"), nullable=False)
    
    # Elo-style ability estimate
    ability = Column(Float, default=1200.0)  # Start at mid-range
    
    # Bayesian Knowledge Tracing parameters
    p_learned = Column(Float, default=0.5)  # Probability student has learned the skill
    p_known = Column(Float, default=0.5)    # Current knowledge probability
    
    # Metadata
    attempts = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    last_attempt = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User")
    topic = relationship("LearningTopic")
