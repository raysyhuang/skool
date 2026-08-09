from sqlalchemy import (
    Column, Integer, String, Float, Text, Date, DateTime, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class LearningTopic(Base):
    """A micro-topic from the Marble Skill Taxonomy (ODbL 1.0 / CC BY-SA 4.0).

    Two kinds of rows live here:

    - **playable** (``question_mode`` set) — a generator can produce and
      auto-grade questions for this topic, so it joins the math/English
      rotation and accumulates per-topic mastery.
    - **reference** (``question_mode`` NULL) — no generator covers it, but the
      assessment prompt is still worth putting in front of a parent.
    """

    __tablename__ = "learning_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_key = Column(String, nullable=False, unique=True, index=True)  # "mt_..."
    subject = Column(String, nullable=False, index=True)   # "Mathematics", "English", ...
    domain = Column(String, nullable=False)                # "Fractions", "Vocabulary", ...
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    topic_type = Column(String, nullable=True)             # CONCEPTUAL / PROCEDURAL / ...
    age_start = Column(Integer, nullable=False)
    age_end = Column(Integer, nullable=False)
    centrality = Column(Float, default=0.0)
    evidence = Column(Text, nullable=True)                 # JSON list of strings
    assessment_prompt = Column(Text, nullable=True)        # contains a {{name}} placeholder
    question_mode = Column(String, nullable=True, index=True)  # generator mode, or NULL

    progress = relationship("UserTopicProgress", back_populates="topic")

    __table_args__ = (
        Index("ix_learning_topics_subject_ages", "subject", "age_start", "age_end"),
    )


class TopicPrerequisite(Base):
    """Directed edge: ``topic_key`` cannot be learned before ``prerequisite_key``."""

    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    topic_key = Column(String, nullable=False, index=True)
    prerequisite_key = Column(String, nullable=False, index=True)
    strength = Column(String, nullable=False, default="hard")  # "hard" or "soft"
    reason = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("topic_key", "prerequisite_key", name="uq_topic_prereq"),
    )


class UserTopicProgress(Base):
    """Per-child SM-2 state for a playable topic.

    Deliberately mirrors UserCharacterProgress field for field so both can be
    driven by app.services.spaced_repetition.
    """

    __tablename__ = "user_topic_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("learning_topics.id"), nullable=False)

    mastery_score = Column(Integer, default=0)   # 0-5, derived from repetitions
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    last_seen = Column(DateTime, nullable=True)

    easiness_factor = Column(Float, default=2.5)
    sm2_interval = Column(Integer, default=0)
    sm2_repetitions = Column(Integer, default=0)
    next_review_date = Column(Date, nullable=True)

    user = relationship("User", back_populates="topic_progress")
    topic = relationship("LearningTopic", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),
    )
