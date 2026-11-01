import json
from datetime import date, timedelta
from collections import defaultdict

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.models.progress import UserCharacterProgress
from app.models.character import Character
from app.models.topic import LearningTopic
from app.services.topic_selection import (
    SUBJECT_BY_GAME_TYPE,
    conversation_prompts,
    topic_snapshot,
    weakest_topics,
)

limiter = Limiter(key_func=get_remote_address)

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

    # Check if taxonomy is loaded
    taxonomy_missing = db.query(LearningTopic).count() == 0

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

        # ── Topic spine (math / English) + offline conversation prompts ──
        topics = topic_snapshot(db, child)
        queued_topics = json.loads(child.pending_drill_topic_ids or "[]")
        for entry in topics:
            entry["drillable"] = bool(weakest_topics(db, child, entry["game_type"]))
            entry["drill_queued"] = any(
                t.id in queued_topics
                for t in weakest_topics(db, child, entry["game_type"], limit=50)
            )
        talk_prompts = conversation_prompts(db, child, limit=3)

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
            "topics": topics,
            "talk_prompts": talk_prompts,
        })

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "children": child_data,
        "taxonomy_missing": taxonomy_missing,
    })


@router.post("/drill/{child_id}")
@limiter.limit("20/minute")
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
        return JSONResponse(
            {"error": f"{child.name} hasn't practiced any characters yet — there's nothing to drill until they play a few sessions."},
            status_code=400,
        )

    # Queue the drill; the child's next Chinese session consumes it.
    # Creating the session here would orphan it (the child always gets a
    # fresh session on login) and pollute their streak/session counters.
    child.pending_drill_char_ids = json.dumps(char_ids)
    db.commit()

    return JSONResponse({
        "queued": True,
        "characters": len(char_ids),
        "child_name": child.name,
    })


@router.post("/drill/{child_id}/cancel")
def cancel_drill(child_id: int, request: Request, db: Session = Depends(get_db)):
    """Cancel a queued drill that hasn't been played yet."""
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    child = db.query(User).filter_by(id=child_id, role="child").first()
    if not child:
        return JSONResponse({"error": "Child not found"}, status_code=404)

    child.pending_drill_char_ids = None
    db.commit()
    return JSONResponse({"cancelled": True})


@router.post("/drill-topics/{child_id}/{game_type}")
@limiter.limit("20/minute")
def start_topic_drill(child_id: int, game_type: str, request: Request, db: Session = Depends(get_db)):
    """Queue a math or English drill on the topics this child is weakest at."""
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    if game_type not in SUBJECT_BY_GAME_TYPE:
        return JSONResponse({"error": f"Cannot drill {game_type}"}, status_code=400)

    child = db.query(User).filter_by(id=child_id, role="child").first()
    if not child:
        return JSONResponse({"error": "Child not found"}, status_code=404)

    topics = weakest_topics(db, child, game_type, limit=5)
    if not topics:
        return JSONResponse(
            {"error": f"{child.name} hasn't practised any {game_type} topics yet — "
                      f"there's nothing to drill until they play a few sessions."},
            status_code=400,
        )

    # Keep any drill already queued for the *other* subject.
    existing = json.loads(child.pending_drill_topic_ids or "[]")
    other_subject_ids = {
        row[0] for row in db.query(LearningTopic.id)
        .filter(LearningTopic.id.in_(existing))
        .filter(LearningTopic.subject != SUBJECT_BY_GAME_TYPE[game_type])
        .all()
    } if existing else set()

    child.pending_drill_topic_ids = json.dumps(
        [t.id for t in topics] + sorted(other_subject_ids)
    )
    db.commit()

    return JSONResponse({
        "queued": True,
        "game_type": game_type,
        "topics": [t.name for t in topics],
        "child_name": child.name,
    })


@router.post("/drill-topics/{child_id}/{game_type}/cancel")
def cancel_topic_drill(child_id: int, game_type: str, request: Request, db: Session = Depends(get_db)):
    """Drop the queued drill for one subject, leaving the other alone."""
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    subject = SUBJECT_BY_GAME_TYPE.get(game_type)
    if subject is None:
        return JSONResponse({"error": f"Cannot drill {game_type}"}, status_code=400)

    child = db.query(User).filter_by(id=child_id, role="child").first()
    if not child:
        return JSONResponse({"error": "Child not found"}, status_code=404)

    queued = json.loads(child.pending_drill_topic_ids or "[]")
    keep = [
        row[0] for row in db.query(LearningTopic.id)
        .filter(LearningTopic.id.in_(queued))
        .filter(LearningTopic.subject != subject)
        .all()
    ] if queued else []

    child.pending_drill_topic_ids = json.dumps(keep) if keep else None
    db.commit()
    return JSONResponse({"cancelled": True})
