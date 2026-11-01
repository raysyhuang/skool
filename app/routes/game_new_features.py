"""New feature routes for PR #14: quests, placement, garage, journey."""

import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, DailyQuest, UserDailyQuestProgress, CollectibleItem, UserCollectible
from app.services.daily_quests import get_daily_quests_for_user, claim_quest_reward, ensure_daily_quests
from app.services.placement import start_placement_test, get_next_placement_question, submit_placement_response, complete_placement_test

router = APIRouter(prefix="/game")
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


@router.get("/daily-quests")
def daily_quests_page(request: Request, db: Session = Depends(get_db)):
    """Daily quests UI."""
    user = get_current_user(request, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "users": []})
    
    ensure_daily_quests(db)
    quests = get_daily_quests_for_user(db, user.id)
    
    return templates.TemplateResponse("daily_quests.html", {
        "request": request,
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


@router.get("/placement-test/{subject}")
def placement_test_page(subject: str, request: Request, db: Session = Depends(get_db)):
    """Placement test UI."""
    user = get_current_user(request, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "users": []})
    
    return templates.TemplateResponse("placement_test.html", {
        "request": request,
        "user": user,
        "subject": subject
    })


@router.post("/placement-test/{subject}/start")
def start_test(subject: str, request: Request, db: Session = Depends(get_db)):
    """Start placement test."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    
    test = start_placement_test(db, user, subject)
    return JSONResponse({"test_id": test.id})


@router.get("/placement-test/{test_id}/next")
def next_question(test_id: int, db: Session = Depends(get_db)):
    """Get next placement test question."""
    from app.models import PlacementTest
    test = db.query(PlacementTest).filter_by(id=test_id).first()
    if not test:
        return JSONResponse({"error": "Test not found"}, status_code=404)
    
    question = get_next_placement_question(db, test)
    
    if not question:
        # Test complete
        results = complete_placement_test(db, test)
        return JSONResponse({"complete": True, **results})
    
    return JSONResponse(question)


@router.post("/placement-test/{test_id}/answer")
def submit_test_answer(test_id: int, request: Request, db: Session = Depends(get_db)):
    """Submit placement test answer."""
    from app.models import PlacementTest
    import asyncio
    
    body = asyncio.run(request.json())
    
    test = db.query(PlacementTest).filter_by(id=test_id).first()
    if not test:
        return JSONResponse({"error": "Test not found"}, status_code=404)
    
    result = submit_placement_response(
        db,
        test,
        body["question_data"],
        body["selected_answer"],
        body.get("response_time_ms", 0)
    )
    
    return JSONResponse(result)


@router.get("/garage")
def garage_page(request: Request, db: Session = Depends(get_db)):
    """Garage collectibles UI."""
    user = get_current_user(request, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "users": []})
    
    # Get all collectibles with ownership status
    items = db.query(CollectibleItem).all()
    user_collectibles = db.query(UserCollectible).filter_by(user_id=user.id).all()
    owned_ids = {uc.item_id for uc in user_collectibles}
    equipped_ids = {uc.item_id for uc in user_collectibles if uc.equipped}
    
    collectibles = []
    for item in items:
        collectibles.append({
            "id": item.id,
            "item_type": item.item_type,
            "name": item.name,
            "emoji": item.emoji,
            "rarity": item.rarity,
            "price_coins": item.price_coins,
            "unlock_requirement": item.unlock_requirement,
            "owned": item.id in owned_ids,
            "equipped": item.id in equipped_ids
        })
    
    return templates.TemplateResponse("garage.html", {
        "request": request,
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
    
    # Unequip others of same type
    db.query(UserCollectible).filter(
        UserCollectible.user_id == user.id,
        UserCollectible.item_id.in_(
            db.query(CollectibleItem.id).filter_by(item_type=item.item_type)
        )
    ).update({"equipped": False}, synchronize_session=False)
    
    # Equip this one
    user_item = db.query(UserCollectible).filter_by(user_id=user.id, item_id=item_id).first()
    if user_item:
        user_item.equipped = True
    
    db.commit()
    return JSONResponse({"success": True})


@router.get("/journey")
def journey_map_page(request: Request, db: Session = Depends(get_db)):
    """Learning journey map UI."""
    user = get_current_user(request, db)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "users": []})
    
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
    
    return templates.TemplateResponse("journey_map.html", {
        "request": request,
        "user": user,
        "nodes": journey_data
    })


@router.get("/dashboard-enhanced")
def enhanced_dashboard(request: Request, db: Session = Depends(get_db)):
    """Enhanced parent dashboard with ability graphs."""
    user = get_current_user(request, db)
    if not user or user.role != "parent":
        return templates.TemplateResponse("login.html", {"request": request, "users": []})
    
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
    
    return templates.TemplateResponse("dashboard_enhanced.html", {
        "request": request,
        "user": user,
        "students": students_data,
        "students_json": json.dumps(students_data)
    })
