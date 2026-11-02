"""New feature routes for PR #14: quests, placement, garage, journey."""

import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from sqlalchemy import func

from app.models import User, DailyQuest, UserDailyQuestProgress, CollectibleItem, UserCollectible
from app.models.session import GameSession
from app.services.daily_quests import get_daily_quests_for_user, claim_quest_reward, ensure_daily_quests

router = APIRouter(prefix="/game")
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


# Icons for garage unlock requirements: kids see "🔥 12/30", not a sentence
_REQUIREMENT_ICONS = {
    "streak": "🔥",
    "sessions": "🏁",
    "perfect_sessions": "🏆",
    "accuracy": "🎯",
}
# Overall accuracy only counts once there's enough play behind it, so one
# lucky 5/5 session can't unlock a legendary item
ACCURACY_MIN_SESSIONS = 10


def _overall_accuracy(db: Session, user_id: int) -> tuple[int, int]:
    """(accuracy %, completed sessions) across all of a user's sessions."""
    correct, wrong, count = db.query(
        func.coalesce(func.sum(GameSession.total_correct), 0),
        func.coalesce(func.sum(GameSession.total_wrong), 0),
        func.count(GameSession.id),
    ).filter(
        GameSession.user_id == user_id, GameSession.completed_at.isnot(None)
    ).one()
    total = correct + wrong
    return (round(correct / total * 100) if total else 0), count


def requirement_status(db: Session, user: User, raw: str | None, _cache: dict | None = None) -> dict | None:
    """Evaluate an item's unlock requirement for a user.

    ``raw`` is CollectibleItem.unlock_requirement: JSON like
    {"type": "streak", "value": 30}. Returns None when there's no
    requirement, else {"met", "label", "current", "target"}. Anything
    unparseable stays locked rather than silently unlocking.
    """
    if not raw:
        return None
    try:
        req = json.loads(raw)
        kind, target = req["type"], int(req["value"])
    except (ValueError, TypeError, KeyError):
        return {"met": False, "label": f"🔒 {raw}", "current": 0, "target": 0}

    if kind == "streak":
        current = max(user.best_streak or 0, user.streak or 0)
    elif kind == "sessions":
        current = user.total_sessions_completed or 0
    elif kind == "perfect_sessions":
        current = user.perfect_sessions or 0
    elif kind == "accuracy":
        cache = _cache if _cache is not None else {}
        if "accuracy" not in cache:
            cache["accuracy"] = _overall_accuracy(db, user.id)
        current, sessions = cache["accuracy"]
        if sessions < ACCURACY_MIN_SESSIONS:
            current = min(current, target - 1)
    else:
        return {"met": False, "label": f"🔒 {raw}", "current": 0, "target": target}

    icon = _REQUIREMENT_ICONS[kind]
    unit = "%" if kind == "accuracy" else ""
    return {
        "met": current >= target,
        "label": f"{icon} {min(current, target)}{unit}/{target}{unit}",
        "current": current,
        "target": target,
    }


def get_equipped_display(db: Session, user: User) -> dict:
    """Emoji for what the user has equipped, for the home screen.

    Car: the garage car if one is equipped, else the store car skin.
    Pet / trail: the garage item ("No Pet" / "No Trail" show nothing),
    the trail falling back to the store trail effect.
    """
    from app.models.store import StoreItem

    rows = (
        db.query(CollectibleItem)
        .join(UserCollectible, UserCollectible.item_id == CollectibleItem.id)
        .filter(UserCollectible.user_id == user.id, UserCollectible.equipped.is_(True))
        .all()
    )
    garage = {
        item.item_type: item for item in rows
        if item.item_key not in ("no_pet", "no_trail", "default")
    }

    def store_emoji(key: str | None) -> str | None:
        if not key:
            return None
        item = db.query(StoreItem).filter_by(key=key).first()
        return item.emoji if item else None

    car = garage.get("car")
    trail = garage.get("trail")
    pet = garage.get("pet")
    return {
        "car": car.emoji if car else store_emoji(user.equipped_car_skin),
        "pet": pet.emoji if pet else None,
        "trail": trail.emoji if trail else store_emoji(user.equipped_trail),
    }


@router.get("/daily-quests")
def daily_quests_page(request: Request, db: Session = Depends(get_db)):
    """Daily quests UI."""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    ensure_daily_quests(db)
    quests = get_daily_quests_for_user(db, user.id)
    
    return templates.TemplateResponse(request, "daily_quests.html", {
        "user": user,
        "quests": quests
    })


@router.post("/claim-quest/{progress_id}")
def claim_quest(progress_id: int, request: Request, db: Session = Depends(get_db)):
    """Claim completed quest reward."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"success": False, "error": "Not logged in"}, status_code=401)
    
    success = claim_quest_reward(db, user.id, progress_id)
    return JSONResponse({"success": success})


# Placement test routes removed: app/services/placement.py is a placeholder
# (one hard-coded "2 + 2" question, fixed grade-3 result) and its writes don't
# match the placement models. Re-add routes once there's a real test behind them.


@router.get("/garage")
def garage_page(request: Request, db: Session = Depends(get_db)):
    """Garage collectibles UI."""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Get all collectibles with ownership status
    items = db.query(CollectibleItem).order_by(CollectibleItem.price_coins, CollectibleItem.id).all()
    user_collectibles = db.query(UserCollectible).filter_by(user_id=user.id).all()
    owned_ids = {uc.item_id for uc in user_collectibles}
    equipped_ids = {uc.item_id for uc in user_collectibles if uc.equipped}
    
    cache: dict = {}
    collectibles = []
    for item in items:
        req = requirement_status(db, user, item.unlock_requirement, cache)
        collectibles.append({
            "id": item.id,
            "item_type": item.item_type,
            "name": item.name,
            "emoji": item.emoji,
            "rarity": item.rarity,
            "price_coins": item.price_coins,
            "requirement": req,
            "locked": bool(req and not req["met"]),
            "owned": item.id in owned_ids,
            "equipped": item.id in equipped_ids
        })
    
    return templates.TemplateResponse(request, "garage.html", {
        "user": user,
        "collectibles": collectibles
    })


@router.post("/garage/buy/{item_id}")
def buy_collectible(item_id: int, request: Request, db: Session = Depends(get_db)):
    """Buy a collectible item."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"success": False, "error": "Not logged in"}, status_code=401)
    
    item = db.query(CollectibleItem).filter_by(id=item_id).first()
    if not item:
        return JSONResponse({"success": False, "error": "Item not found"}, status_code=404)

    # Lock the user before checking coins/ownership: two taps on two gunicorn
    # workers could otherwise both pass and spend the same coins twice
    user = db.query(User).filter_by(id=user.id).with_for_update().populate_existing().one()

    req = requirement_status(db, user, item.unlock_requirement)
    if req and not req["met"]:
        return JSONResponse({"success": False, "error": "Locked", "requirement": req["label"]}, status_code=403)

    if user.coins < item.price_coins:
        return JSONResponse({"success": False, "error": "Not enough coins"}, status_code=400)
    
    # Check if already owned
    existing = db.query(UserCollectible).filter_by(user_id=user.id, item_id=item_id).first()
    if existing:
        return JSONResponse({"success": False, "error": "Already owned"}, status_code=400)
    
    # Purchase
    user.coins -= item.price_coins
    collectible = UserCollectible(user_id=user.id, item_id=item_id, equipped=False)
    db.add(collectible)
    db.commit()
    
    return JSONResponse({"success": True, "coins": user.coins})


@router.post("/garage/equip/{item_id}")
def equip_collectible(item_id: int, request: Request, db: Session = Depends(get_db)):
    """Equip a collectible item."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"success": False, "error": "Not logged in"}, status_code=401)
    
    item = db.query(CollectibleItem).filter_by(id=item_id).first()
    if not item:
        return JSONResponse({"success": False}, status_code=404)
    
    # Check ownership before touching anything already equipped
    user_item = db.query(UserCollectible).filter_by(user_id=user.id, item_id=item_id).first()
    if not user_item:
        return JSONResponse({"success": False, "error": "Not owned"}, status_code=403)

    req = requirement_status(db, user, item.unlock_requirement)
    if req and not req["met"]:
        return JSONResponse({"success": False, "error": "Locked", "requirement": req["label"]}, status_code=403)

    # Unequip others of same type
    db.query(UserCollectible).filter(
        UserCollectible.user_id == user.id,
        UserCollectible.item_id.in_(
            db.query(CollectibleItem.id).filter_by(item_type=item.item_type)
        )
    ).update({"equipped": False}, synchronize_session=False)
    
    user_item.equipped = True
    
    db.commit()
    return JSONResponse({"success": True})


@router.get("/journey")
def journey_map_page(request: Request, db: Session = Depends(get_db)):
    """Learning journey map UI."""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    from app.models import JourneyNode, UserJourneyProgress
    
    # Get all nodes with user progress
    nodes = db.query(JourneyNode).order_by(JourneyNode.order_index).all()
    
    journey_data = []
    for node in nodes:
        progress = db.query(UserJourneyProgress).filter_by(
            user_id=user.id,
            node_id=node.id
        ).first()
        
        if not progress:
            progress = UserJourneyProgress(
                user_id=user.id,
                node_id=node.id,
                unlocked=(node.order_index == 0)  # First node unlocked
            )
            db.add(progress)
        
        completion_req = json.loads(node.completion_requirement) if node.completion_requirement else {}
        
        journey_data.append({
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "emoji": node.emoji,
            "completion_requirement": completion_req,
            "progress": progress
        })
    
    db.commit()
    
    return templates.TemplateResponse(request, "journey_map.html", {
        "user": user,
        "nodes": journey_data
    })


@router.get("/dashboard-enhanced")
def enhanced_dashboard(request: Request, db: Session = Depends(get_db)):
    """Enhanced parent dashboard with ability graphs."""
    user = get_current_user(request, db)
    if not user or user.role != "parent":
        return RedirectResponse(url="/login", status_code=303)
    
    from app.models import SkillAbility, UserTopicProgress, GameSession
    from datetime import datetime, timedelta
    
    # Get all children
    students = db.query(User).filter_by(role="child").all()
    
    students_data = []
    for student in students:
        # Calculate stats
        sessions = db.query(GameSession).filter_by(user_id=student.id).all()
        total_sessions = len(sessions)
        total_correct = sum(s.total_correct for s in sessions)
        total_questions = sum(s.total_correct + s.total_wrong for s in sessions)
        accuracy = round((total_correct / total_questions * 100) if total_questions > 0 else 0)
        
        # Get mastery counts
        topic_progress = db.query(UserTopicProgress).filter_by(user_id=student.id).all()
        mastered = sum(1 for tp in topic_progress if tp.mastery_score >= 4)
        learning = sum(1 for tp in topic_progress if 1 <= tp.mastery_score < 4)
        new = sum(1 for tp in topic_progress if tp.mastery_score < 1)
        
        # Get ability data
        abilities = db.query(SkillAbility).filter_by(user_id=student.id).all()
        math_abilities = [a for a in abilities if a.topic and a.topic.subject == "math"]
        english_abilities = [a for a in abilities if a.topic and a.topic.subject == "english"]
        
        # Weekly activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = [s for s in sessions if s.started_at and s.started_at > week_ago]
        weekly_sessions = [0] * 7
        for s in recent_sessions:
            day_idx = (s.started_at.weekday() + 1) % 7  # Make Monday = 0
            weekly_sessions[day_idx] += 1
        
        students_data.append({
            "id": student.id,
            "name": student.name,
            "stats": {
                "total_sessions": total_sessions,
                "accuracy": accuracy,
                "streak": student.streak,
                "mastered_skills": mastered
            },
            "mastered_count": mastered,
            "learning_count": learning,
            "new_count": new,
            "math_ability": [a.ability for a in math_abilities[:10]],
            "english_ability": [a.ability for a in english_abilities[:10]],
            "ability_dates": list(range(1, 11)),
            "weekly_sessions": weekly_sessions,
            "chinese_acc": 85,  # Placeholder
            "math_acc": 78,
            "english_acc": 82,
            "logic_acc": 90
        })
    
    return templates.TemplateResponse(request, "dashboard_enhanced.html", {
        "user": user,
        "students": students_data,
        "students_json": json.dumps(students_data)
    })
