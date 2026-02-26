import os
from datetime import date, timedelta
from collections import defaultdict

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.models.progress import UserCharacterProgress
from app.models.character import Character

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="templates")


def _get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return RedirectResponse(url="/game/", status_code=303)

    # Get all child users
    children = db.query(User).filter_by(role="child").all()

    child_data = []
    for child in children:
        # Basic stats
        total_sessions = (
            db.query(GameSession)
            .filter_by(user_id=child.id)
            .filter(GameSession.completed_at.isnot(None))
            .count()
        )

        # Accuracy
        total_correct = (
            db.query(func.sum(GameSession.total_correct))
            .filter_by(user_id=child.id)
            .filter(GameSession.completed_at.isnot(None))
            .scalar() or 0
        )
        total_questions_count = (
            db.query(func.count(SessionQuestion.id))
            .join(GameSession)
            .filter(GameSession.user_id == child.id)
            .filter(GameSession.completed_at.isnot(None))
            .scalar() or 0
        )
        accuracy = round(total_correct / total_questions_count * 100) if total_questions_count else 0

        # Last 7 days activity
        today = date.today()
        week_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count = (
                db.query(GameSession)
                .filter_by(user_id=child.id)
                .filter(GameSession.completed_at.isnot(None))
                .filter(func.date(GameSession.started_at) == d)
                .count()
            )
            week_data.append({"day": d.strftime("%a"), "count": count})

        max_day = max(w["count"] for w in week_data) if week_data else 1
        for w in week_data:
            w["pct"] = round(w["count"] / max(max_day, 1) * 100)

        # Mastery distribution
        mastery_dist = defaultdict(int)
        progress = db.query(UserCharacterProgress).filter_by(user_id=child.id).all()
        for p in progress:
            mastery_dist[p.mastery_score] += 1

        mastery_bars = []
        for level in range(6):
            mastery_bars.append({"level": level, "count": mastery_dist.get(level, 0)})

        # Weakest characters
        weak_chars = (
            db.query(UserCharacterProgress, Character)
            .join(Character, UserCharacterProgress.character_id == Character.id)
            .filter(UserCharacterProgress.user_id == child.id)
            .order_by(UserCharacterProgress.mastery_score.asc())
            .limit(10)
            .all()
        )
        weakest = [
            {
                "character": char.character,
                "pinyin": char.pinyin,
                "meaning": char.meaning,
                "mastery": prog.mastery_score,
            }
            for prog, char in weak_chars
        ]

        child_data.append({
            "user": child,
            "total_sessions": total_sessions,
            "accuracy": accuracy,
            "week_data": week_data,
            "mastery_bars": mastery_bars,
            "weakest": weakest,
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "children": child_data,
    })
