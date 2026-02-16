from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String, nullable=False)          # e.g. "大"
    pinyin = Column(String, nullable=False)              # e.g. "dà"
    meaning = Column(String, nullable=False)             # e.g. "big"
    difficulty = Column(Integer, nullable=False)         # 1-3 (tier)
    tags = Column(String, nullable=True)                 # comma-separated: "animal,nature"
    image_url = Column(String, nullable=True)            # path to picture for matching
    sentence_template = Column(String, nullable=True)    # "这只___很大" (for daughter's mode)
    explanation = Column(String, nullable=True)          # micro-explanation for wrong answers
    target_users = Column(String, nullable=False, default="all")  # "son", "daughter", "all"

    # Relationships
    progress = relationship("UserCharacterProgress", back_populates="character")
