"""Daily quest service: quest generation, progress tracking, rewards."""

from datetime import date
from sqlalchemy.orm import Session
from app.models import DailyQuest, UserDailyQuestProgress, User
# Reward logic inline

# Quest definitions (can later be loaded from DB or config)
DAILY_QUEST_POOL = [
    {
        "quest_type": "play_session",
        "title": "Daily Practice",
        "description": "Complete 1 session today",
        "target_value": 1,
        "reward_type": "stars",
        "reward_amount": 5,
        "icon": "⭐"
    },
    {
        "quest_type": "perfect_session",
        "title": "Perfect Score",
        "description": "Get 5/5 correct in one session",
        "target_value": 1,
        "reward_type": "stars",
        "reward_amount": 10,
        "icon": "🏆"
    },
    {
        "quest_type": "combo_master",
        "title": "Combo Master",
        "description": "Reach a 3+ answer combo",
        "target_value": 3,
        "reward_type": "stars",
        "reward_amount": 8,
        "icon": "🔥"
    },
    {
        "quest_type": "streak_keeper",
        "title": "Streak Keeper",
        "description": "Maintain a 3+ day streak",
        "target_value": 3,
        "reward_type": "coins",
        "reward_amount": 1,
        "icon": "📅"
    },
]


def ensure_daily_quests(db: Session) -> None:
    """Ensure core quest definitions exist in the database."""
    for quest_data in DAILY_QUEST_POOL:
        existing = db.query(DailyQuest).filter(
            DailyQuest.quest_type == quest_data["quest_type"]
        ).first()
        
        if not existing:
            quest = DailyQuest(**quest_data)
            db.add(quest)
    
    db.commit()


def get_daily_quests_for_user(db: Session, user_id: int) -> list[dict]:
    """Return today's quests for a user with progress."""
    today = date.today()
    
    # Get all quest definitions
    quests = db.query(DailyQuest).all()
    
    result = []
    for quest in quests:
        # Find or create progress record for today
        progress = db.query(UserDailyQuestProgress).filter(
            UserDailyQuestProgress.user_id == user_id,
            UserDailyQuestProgress.quest_id == quest.id,
            UserDailyQuestProgress.date == today
        ).first()
        
        if not progress:
            progress = UserDailyQuestProgress(
                user_id=user_id,
                quest_id=quest.id,
                date=today,
                current_value=0,
                completed=False,
                claimed=False
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
        
        result.append({
            "id": quest.id,
            "quest_type": quest.quest_type,
            "title": quest.title,
            "description": quest.description,
            "target_value": quest.target_value,
            "current_value": progress.current_value,
            "completed": progress.completed,
            "claimed": progress.claimed,
            "reward_type": quest.reward_type,
            "reward_amount": quest.reward_amount,
            "icon": quest.icon,
            "progress_id": progress.id
        })
    
    return result


def update_quest_progress(
    db: Session,
    user_id: int,
    quest_type: str,
    increment: int = 1
) -> dict | None:
    """Update progress for a specific quest type. Returns quest data if newly completed."""
    today = date.today()
    
    quest = db.query(DailyQuest).filter(
        DailyQuest.quest_type == quest_type
    ).first()
    
    if not quest:
        return None
    
    progress = db.query(UserDailyQuestProgress).filter(
        UserDailyQuestProgress.user_id == user_id,
        UserDailyQuestProgress.quest_id == quest.id,
        UserDailyQuestProgress.date == today
    ).first()
    
    if not progress:
        progress = UserDailyQuestProgress(
            user_id=user_id,
            quest_id=quest.id,
            date=today,
            current_value=0,
            completed=False,
            claimed=False
        )
        db.add(progress)
    
    if progress.completed:
        return None  # Already completed
    
    progress.current_value += increment
    
    if progress.current_value >= quest.target_value and not progress.completed:
        progress.completed = True
        from datetime import datetime, timezone
        progress.completed_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "quest_type": quest.quest_type,
            "title": quest.title,
            "reward_type": quest.reward_type,
            "reward_amount": quest.reward_amount,
            "icon": quest.icon
        }
    
    db.commit()
    return None


def claim_quest_reward(db: Session, user_id: int, progress_id: int) -> bool:
    """Claim reward for a completed quest."""
    progress = db.query(UserDailyQuestProgress).filter(
        UserDailyQuestProgress.id == progress_id,
        UserDailyQuestProgress.user_id == user_id
    ).first()
    
    if not progress or not progress.completed or progress.claimed:
        return False
    
    quest = db.query(DailyQuest).filter(
        DailyQuest.id == progress.quest_id
    ).first()
    
    if not quest:
        return False
    
    # Award the reward
    user = db.query(User).filter(User.id == user_id).first()
    award_currency(
        db=db,
        user=user,
        reward_type=quest.reward_type,
        amount=quest.reward_amount,
        reason=f"Daily quest: {quest.title}"
    )
    
    progress.claimed = True
    db.commit()
    
    return True
