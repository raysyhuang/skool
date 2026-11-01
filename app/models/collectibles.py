"""Collectible items: cars, pets, themes for the garage."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class CollectibleItem(Base):
    """Collectible items available in the garage."""
    __tablename__ = "collectible_items"
    
    id = Column(Integer, primary_key=True, index=True)
    item_type = Column(String, nullable=False)  # "car", "pet", "theme", "trail"
    item_key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    emoji = Column(String, nullable=True)
    rarity = Column(String, default="common")  # "common", "rare", "epic", "legendary"
    price_coins = Column(Integer, default=0)
    unlock_requirement = Column(String, nullable=True)  # JSON: {"type": "streak", "value": 7}


class UserCollectible(Base):
    """User's collected items."""
    __tablename__ = "user_collectibles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("collectible_items.id"), nullable=False)
    unlocked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    equipped = Column(Boolean, default=False)
    
    user = relationship("User")
    item = relationship("CollectibleItem")


class JourneyNode(Base):
    """Learning journey map nodes (islands, milestones)."""
    __tablename__ = "journey_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_key = Column(String, unique=True, nullable=False)
    node_type = Column(String, nullable=False)  # "island", "checkpoint", "boss"
    subject = Column(String, nullable=False)  # "math", "english", "chinese", "mixed"
    order_index = Column(Integer, nullable=False)
    
    # Display
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    emoji = Column(String, nullable=True)
    
    # Requirements
    unlock_requirement = Column(String, nullable=True)  # JSON
    completion_requirement = Column(String, nullable=True)  # JSON: {"sessions": 5, "accuracy": 0.8}


class UserJourneyProgress(Base):
    """User's progress through the learning journey."""
    __tablename__ = "user_journey_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("journey_nodes.id"), nullable=False)
    
    unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    sessions_completed = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    
    user = relationship("User")
    node = relationship("JourneyNode")
