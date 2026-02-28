import os
from datetime import date, timedelta
from collections import defaultdict

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
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
    today = date.today()

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

        # ── Activity Heatmap (last 30 days) ──
        heatmap = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            count = (
                db.query(GameSession)
                .filter_by(user_id=child.id)
                .filter(GameSession.completed_at.isnot(None))
                .filter(func.date(GameSession.started_at) == d)
                .count()
            )
            heatmap.append({"date": d.isoformat(), "day_label": d.strftime("%d"), "count": count})

        # ── Session History (last 10 sessions) ──
        recent_sessions = (
            db.query(GameSession)
            .filter_by(user_id=child.id)
            .filter(GameSession.completed_at.isnot(None))
            .order_by(GameSession.completed_at.desc())
            .limit(10)
            .all()
        )
        session_history = []
        for s in recent_sessions:
            q_count = len(s.questions) if s.questions else 0
            duration_secs = None
            if s.started_at and s.completed_at:
                sa = s.started_at.replace(tzinfo=None)
                ca = s.completed_at.replace(tzinfo=None)
                duration_secs = int((ca - sa).total_seconds())
            session_history.append({
                "date": s.completed_at.strftime("%b %d") if s.completed_at else "—",
                "game_type": (s.game_type or "chinese").capitalize(),
                "score": f"{s.total_correct}/{q_count}",
                "duration": f"{duration_secs // 60}m {duration_secs % 60}s" if duration_secs and duration_secs > 0 else "—",
            })

        # ── Review Schedule (SM-2) ──
        tomorrow = today + timedelta(days=1)
        end_of_week = today + timedelta(days=7)

        due_today = (
            db.query(func.count(UserCharacterProgress.id))
            .filter(UserCharacterProgress.user_id == child.id)
            .filter(UserCharacterProgress.next_review_date <= today)
            .scalar() or 0
        )
        due_tomorrow = (
            db.query(func.count(UserCharacterProgress.id))
            .filter(UserCharacterProgress.user_id == child.id)
            .filter(UserCharacterProgress.next_review_date == tomorrow)
            .scalar() or 0
        )
        due_this_week = (
            db.query(func.count(UserCharacterProgress.id))
            .filter(UserCharacterProgress.user_id == child.id)
            .filter(UserCharacterProgress.next_review_date <= end_of_week)
            .scalar() or 0
        )

        # Characters due today (up to 8)
        due_today_chars = (
            db.query(UserCharacterProgress, Character)
            .join(Character, UserCharacterProgress.character_id == Character.id)
            .filter(UserCharacterProgress.user_id == child.id)
            .filter(UserCharacterProgress.next_review_date <= today)
            .order_by(UserCharacterProgress.next_review_date.asc())
            .limit(8)
            .all()
        )
        due_chars = [
            {"character": char.character, "pinyin": char.pinyin, "meaning": char.meaning}
            for prog, char in due_today_chars
        ]

        review_schedule = {
            "due_today": due_today,
            "due_tomorrow": due_tomorrow,
            "due_this_week": due_this_week,
            "due_chars": due_chars,
        }

        child_data.append({
            "user": child,
            "total_sessions": total_sessions,
            "accuracy": accuracy,
            "week_data": week_data,
            "mastery_bars": mastery_bars,
            "weakest": weakest,
            "heatmap": heatmap,
            "session_history": session_history,
            "review_schedule": review_schedule,
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "children": child_data,
    })


@router.post("/drill/{child_id}")
def start_drill(child_id: int, request: Request, db: Session = Depends(get_db)):
    """Start a drill session targeting the child's weakest/overdue characters."""
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    child = db.query(User).filter_by(id=child_id, role="child").first()
    if not child:
        return JSONResponse({"error": "Child not found"}, status_code=404)

    today = date.today()

    # Get overdue character IDs first, then weakest
    overdue = (
        db.query(UserCharacterProgress.character_id)
        .filter(UserCharacterProgress.user_id == child.id)
        .filter(UserCharacterProgress.next_review_date <= today)
        .order_by(UserCharacterProgress.next_review_date.asc())
        .limit(10)
        .all()
    )
    char_ids = [row[0] for row in overdue]

    # If not enough overdue, add weakest characters
    if len(char_ids) < 5:
        weak = (
            db.query(UserCharacterProgress.character_id)
            .filter(UserCharacterProgress.user_id == child.id)
            .filter(UserCharacterProgress.character_id.notin_(char_ids) if char_ids else True)
            .order_by(UserCharacterProgress.mastery_score.asc())
            .limit(10 - len(char_ids))
            .all()
        )
        char_ids.extend(row[0] for row in weak)

    if not char_ids:
        return JSONResponse({"error": "No characters to drill"}, status_code=400)

    from app.services.session_engine import create_session
    try:
        session = create_session(db, child, game_type="chinese", character_ids=char_ids)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    return JSONResponse({
        "session_id": session.id,
        "redirect": f"/game/chinese",
        "characters": len(char_ids),
    })
