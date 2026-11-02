import json
from datetime import date, datetime, timedelta, timezone
from collections import Counter, defaultdict

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.models.progress import UserCharacterProgress
from app.models.character import Character
from app.models.topic import LearningTopic
from app.models.content_report import ContentReport
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


INSIGHT_DAYS = 14

# Which kind of value each Chinese mode stores in correct/selected_answer.
_CHINESE_ANSWER_KIND = {
    "char_to_image": "image",
    "char_to_meaning": "meaning",
}


def _first_attempt_correct(q: SessionQuestion) -> bool:
    """First-attempt correctness; older rows predate the column, so fall back."""
    val = getattr(q, "first_attempt_correct", None)
    return bool(q.is_correct) if val is None else bool(val)


class _CharLookup:
    """Resolves stored Chinese answers (character / meaning / image_url) to chars."""

    def __init__(self, db: Session):
        chars = db.query(Character).all()
        self.by_char = {c.character: c for c in chars}
        self.by_meaning = {c.meaning: c for c in chars}
        self.by_image = {c.image_url: c for c in chars if c.image_url}

    def readable(self, value: str | None, mode: str | None) -> dict:
        if value is None:
            return {"text": "—", "image": None}
        kind = _CHINESE_ANSWER_KIND.get(mode or "", "character")
        if kind == "image" or value.startswith("/static/"):
            char = self.by_image.get(value) or self.by_meaning.get(value)
            if value.startswith("/static/"):
                label = char.meaning if char else value.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                return {"text": label, "image": value}
            return {"text": value, "image": None}
        if kind == "meaning":
            char = self.by_meaning.get(value)
            return {"text": f"{value} ({char.character})" if char else value, "image": None}
        char = self.by_char.get(value)
        return {"text": f"{value} ({char.meaning})" if char else value, "image": None}


def _readable(value: str | None, game_type: str, mode: str | None, chars: _CharLookup) -> dict:
    if game_type == "chinese":
        return chars.readable(value, mode)
    return {"text": value if value is not None else "—", "image": None}


def _prompt_text(q: SessionQuestion, game_type: str) -> str:
    if game_type == "chinese":
        if q.character is not None:
            return f"{q.character.character} ({q.character.meaning})"
        return ""
    try:
        pd = json.loads(q.prompt_data) if q.prompt_data else {}
    except (ValueError, TypeError):
        pd = {}
    return pd.get("expression") or pd.get("prompt_text") or ""


def _first_pick(q: SessionQuestion) -> str | None:
    return q.first_selected_answer or q.selected_answer


def question_insights(db: Session, child: User, chars: _CharLookup) -> dict:
    """First-try vs eventual accuracy, hint rate and common confusions (14 days)."""
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=INSIGHT_DAYS)
    rows = (
        db.query(SessionQuestion, GameSession.game_type)
        .join(GameSession, SessionQuestion.session_id == GameSession.id)
        .filter(GameSession.user_id == child.id)
        .filter(SessionQuestion.selected_answer.isnot(None))
        .filter(GameSession.started_at >= since)
        .order_by(SessionQuestion.answered_at.desc(), SessionQuestion.id.desc())
        .all()
    )
    answered = len(rows)
    first_ok = sum(1 for q, _ in rows if _first_attempt_correct(q))
    eventual_ok = sum(1 for q, _ in rows if q.is_correct)
    hinted = sum(1 for q, _ in rows if q.hint_shown)

    def pct(n: int) -> int | None:
        return round(n / answered * 100) if answered else None

    # The first pick is what was confused; a successful retry overwrites
    # selected_answer, so rows from before first_selected_answer existed
    # only show misses that stayed wrong.
    wrong = [
        (q, gt or "chinese") for q, gt in rows
        if _first_pick(q) != q.correct_answer
    ]

    counts: Counter = Counter()
    sample: dict[tuple, tuple[SessionQuestion, str]] = {}
    for q, gt in wrong:
        key = (gt, q.correct_answer, _first_pick(q))
        counts[key] += 1
        sample.setdefault(key, (q, gt))

    confusions = []
    for key, n in counts.most_common(5):
        q, gt = sample[key]
        confusions.append({
            "game_type": gt,
            "count": n,
            "prompt": _prompt_text(q, gt),
            "correct": _readable(q.correct_answer, gt, q.question_mode, chars),
            "selected": _readable(_first_pick(q), gt, q.question_mode, chars),
            "char_id": q.character_id if gt == "chinese" else None,
            "topic_id": q.topic_id if gt in SUBJECT_BY_GAME_TYPE else None,
        })

    recent_wrong = [
        {
            "id": q.id,
            "game_type": gt,
            "mode": q.question_mode,
            "prompt": _prompt_text(q, gt),
            "correct": _readable(q.correct_answer, gt, q.question_mode, chars),
            "selected": _readable(_first_pick(q), gt, q.question_mode, chars),
        }
        for q, gt in wrong[:8]
    ]

    return {
        "days": INSIGHT_DAYS,
        "answered": answered,
        "first_try_pct": pct(first_ok),
        "eventual_pct": pct(eventual_ok),
        "hint_pct": pct(hinted),
        "confusions": confusions,
        "recent_wrong": recent_wrong,
    }


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.role != "parent":
        return RedirectResponse(url="/game/", status_code=303)

    # Check if taxonomy is loaded
    taxonomy_missing = db.query(LearningTopic).count() == 0

    # Get all child users
    children = db.query(User).filter_by(role="child").all()
    today = date.today()
    chars = _CharLookup(db)
    reported_ids = {
        row[0] for row in db.query(ContentReport.session_question_id)
        .filter(ContentReport.resolved.is_(False)).all()
    }
    child_names = {c.id: c.name for c in children}
    open_reports = [
        {
            "id": r.id,
            "child_name": child_names.get(r.user_id, "?"),
            "mode": r.mode,
            "prompt": r.prompt,
            "correct": r.correct_answer,
            "selected": r.selected_answer,
            "note": r.note,
            "date": r.created_at.strftime("%b %d") if r.created_at else "—",
        }
        for r in db.query(ContentReport)
        .filter(ContentReport.resolved.is_(False))
        .order_by(ContentReport.created_at.desc())
        .all()
    ]

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
            "insights": question_insights(db, child, chars),
        })

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "children": child_data,
        "taxonomy_missing": taxonomy_missing,
        "open_reports": open_reports,
        "reported_ids": reported_ids,
    })


@router.post("/drill/{child_id}")
@limiter.limit("20/minute")
def start_drill(child_id: int, request: Request, char_id: int | None = None,
                db: Session = Depends(get_db)):
    """Start a drill session targeting the child's weakest/overdue characters.

    With ``char_id`` (an "Often confuses" row), that character leads the drill
    and the rest is topped up to one session's worth, so it is guaranteed a slot.
    """
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    child = db.query(User).filter_by(id=child_id, role="child").first()
    if not child:
        return JSONResponse({"error": "Child not found"}, status_code=404)

    today = date.today()

    focus: list[int] = []
    if char_id is not None:
        if db.query(Character.id).filter_by(id=char_id).first() is None:
            return JSONResponse({"error": "Character not found"}, status_code=404)
        focus = [char_id]

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

    if focus:
        # select_characters samples min(count, pool); a pool of exactly one
        # session keeps the focus character in it.
        per_session = get_settings().questions_per_session
        char_ids = focus + [c for c in char_ids if c != char_id][:per_session - 1]

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
def start_topic_drill(child_id: int, game_type: str, request: Request,
                      topic_id: int | None = None, db: Session = Depends(get_db)):
    """Queue a math or English drill on the topics this child is weakest at.

    With ``topic_id`` the drill is that one topic (drills cycle topics to fill
    the session, so it gets every question).
    """
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    if game_type not in SUBJECT_BY_GAME_TYPE:
        return JSONResponse({"error": f"Cannot drill {game_type}"}, status_code=400)

    child = db.query(User).filter_by(id=child_id, role="child").first()
    if not child:
        return JSONResponse({"error": "Child not found"}, status_code=404)

    if topic_id is not None:
        topic = (
            db.query(LearningTopic)
            .filter_by(id=topic_id, subject=SUBJECT_BY_GAME_TYPE[game_type])
            .filter(LearningTopic.question_mode.isnot(None))
            .first()
        )
        if topic is None:
            return JSONResponse({"error": "Topic not found"}, status_code=404)
        topics = [topic]
    else:
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



class ReportIn(BaseModel):
    note: str | None = Field(default=None, max_length=500)


@router.post("/report/{question_id}")
def report_question(question_id: int, request: Request, body: ReportIn | None = None,
                    db: Session = Depends(get_db)):
    """Flag an asked question as looking wrong, snapshotting what was shown."""
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    q = db.query(SessionQuestion).filter_by(id=question_id).first()
    if not q:
        return JSONResponse({"error": "Question not found"}, status_code=404)

    existing = (
        db.query(ContentReport)
        .filter_by(session_question_id=q.id, resolved=False)
        .first()
    )
    if existing:
        return JSONResponse({"reported": True, "id": existing.id})

    game_type = q.session.game_type or "chinese"
    note = (body.note or "").strip() if body else ""
    report = ContentReport(
        user_id=q.session.user_id,
        session_question_id=q.id,
        mode=q.question_mode,
        prompt=_prompt_text(q, game_type) or None,
        correct_answer=q.correct_answer,
        selected_answer=_first_pick(q),
        note=note or None,
    )
    db.add(report)
    db.commit()
    return JSONResponse({"reported": True, "id": report.id})


@router.post("/report/{report_id}/resolve")
def toggle_report_resolved(report_id: int, request: Request, db: Session = Depends(get_db)):
    """Flip a content report between open and resolved."""
    user = _get_current_user(request, db)
    if not user or user.role != "parent":
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    report = db.query(ContentReport).filter_by(id=report_id).first()
    if not report:
        return JSONResponse({"error": "Report not found"}, status_code=404)

    report.resolved = not report.resolved
    db.commit()
    return JSONResponse({"id": report.id, "resolved": report.resolved})
