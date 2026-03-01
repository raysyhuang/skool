import json
import os
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.session import GameSession, SessionQuestion
from app.services.session_engine import create_session, submit_answer, complete_session, can_start_session, SessionLimitReached

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")

router = APIRouter(prefix="/game")
templates = Jinja2Templates(directory="templates")


def resolve_theme_template(user_theme: str, template_name: str) -> str:
    """Return themed template path, falling back to racing if it doesn't exist."""
    theme = user_theme or "racing"
    path = f"themes/{theme}/{template_name}"
    if os.path.exists(os.path.join(TEMPLATES_DIR, path)):
        return path
    return f"themes/racing/{template_name}"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


def _build_questions_json(questions, db=None, user_id=None) -> list[dict]:
    """Build the questions data list for the frontend, including extra fields for new modes."""
    # Get mastery map if db provided
    mastery_map = {}
    if db and user_id:
        from app.models.progress import UserCharacterProgress
        progress = db.query(UserCharacterProgress).filter_by(user_id=user_id).all()
        mastery_map = {p.character_id: p.mastery_score for p in progress}

    result = []
    for q in questions:
        mode = q.question_mode or "char_to_image"
        opts = json.loads(q.options)
        entry = {
            "id": q.id,
            "question_number": q.question_number,
            "character": q.character.character,
            "pinyin": q.character.pinyin,
            "meaning": q.character.meaning,
            "image_url": q.character.image_url,
            "options": opts,
            "correct_answer": q.correct_answer,
            "mode": mode,
            "mastery": mastery_map.get(q.character_id, 0),
        }
        # Extra fields are encoded in the options JSON for special modes
        # For true_or_false: correct_answer is "true"/"false", options are ["true","false"]
        # The shown_meaning needs to be passed — we derive it:
        if mode == "true_or_false":
            # Options stored as: ["true", "false", shown_meaning, shown_image_or_empty]
            if len(opts) >= 4:
                entry["shown_meaning"] = opts[2]
                entry["shown_image"] = opts[3] if opts[3] else None
                entry["options"] = opts[:2]
            elif len(opts) >= 3:
                entry["shown_meaning"] = opts[2]
                entry["shown_image"] = None
                entry["options"] = opts[:2]
            else:
                entry["shown_meaning"] = q.character.meaning
                entry["shown_image"] = None
        if mode == "fill_in_blank":
            # For fill_in_blank, options stores: [char_options..., display_word, meaning_hint]
            # Last two elements are metadata
            if len(opts) > 2:
                entry["display_word"] = opts[-2]
                entry["meaning_hint"] = opts[-1]
                entry["options"] = opts[:-2]
            else:
                entry["display_word"] = q.character.character
                entry["meaning_hint"] = q.character.meaning
        result.append(entry)
    return result


def _build_generic_questions_json(questions) -> list[dict]:
    """Build questions data for math/logic games (no Character relationship)."""
    result = []
    for q in questions:
        mode = q.question_mode or "unknown"
        opts = json.loads(q.options)
        pd = json.loads(q.prompt_data) if q.prompt_data else {}
        entry = {
            "id": q.id,
            "question_number": q.question_number,
            "character": pd.get("expression", ""),
            "pinyin": pd.get("prompt_text", ""),
            "meaning": pd.get("prompt_text", ""),
            "image_url": None,
            "options": opts,
            "correct_answer": q.correct_answer,
            "mode": mode,
            # Math/logic specific fields
            "expression": pd.get("expression", ""),
            "prompt_text": pd.get("prompt_text", ""),
            "prompt_image": pd.get("prompt_image"),
        }
        result.append(entry)
    return result


def _start_game_session(request: Request, db: Session, game_type: str):
    """Shared logic for starting a game session of any type."""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    user.reset_daily_if_needed()
    db.commit()

    if not can_start_session(user):
        return templates.TemplateResponse(resolve_theme_template(user.theme, "limit_reached.html"), {
            "request": request,
            "user": user,
        })

    try:
        session = create_session(db, user, game_type=game_type)
    except SessionLimitReached:
        return templates.TemplateResponse(resolve_theme_template(user.theme, "limit_reached.html"), {
            "request": request,
            "user": user,
        })
    except ValueError as e:
        request.session["game_error"] = str(e)
        return RedirectResponse(url="/game/", status_code=303)

    questions = session.questions
    first_q = questions[0]
    options = json.loads(first_q.options)

    # Build questions JSON — Chinese uses character relationship, math/logic use prompt_data
    if game_type == "chinese":
        questions_json = json.dumps(_build_questions_json(questions, db=db, user_id=user.id))
        character = first_q.character
    else:
        questions_json = json.dumps(_build_generic_questions_json(questions))
        # Dummy character object for Jinja SSR (racing.js overwrites immediately)
        pd = json.loads(first_q.prompt_data) if first_q.prompt_data else {}
        character = type("DummyChar", (), {
            "character": pd.get("expression", ""),
            "pinyin": pd.get("prompt_text", ""),
            "meaning": pd.get("prompt_text", ""),
            "image_url": None,
        })()

    car_info = CAR_TIERS[min(user.car_level, len(CAR_TIERS) - 1)]

    return templates.TemplateResponse(resolve_theme_template(user.theme, "game.html"), {
        "request": request,
        "user": user,
        "session": session,
        "question": first_q,
        "character": character,
        "options": options,
        "question_number": first_q.question_number,
        "total_questions": len(questions),
        "questions_json": questions_json,
        "game_type": game_type,
        "car_info": car_info,
    })


def _get_today_points(db: Session, user_id: int) -> int:
    """Sum points earned today."""
    from app.models.rewards import PointsLedger
    from datetime import date as date_cls
    today = date_cls.today()
    entries = db.query(PointsLedger).filter_by(user_id=user_id).all()
    return sum(e.change for e in entries if e.created_at and e.created_at.date() == today)


def _get_motivational_message(streak: int) -> str:
    """Pick a motivational message based on streak."""
    from datetime import datetime as dt
    hour = dt.now().hour
    if streak >= 7:
        msgs = ["You're on FIRE!", "Unstoppable!", "Champion mode!"]
    elif streak >= 3:
        msgs = ["Great streak!", "Keep it going!", "You're crushing it!"]
    elif hour < 12:
        msgs = ["Good morning!", "Rise and shine!", "Let's learn!"]
    elif hour < 18:
        msgs = ["Good afternoon!", "Keep learning!", "You've got this!"]
    else:
        msgs = ["Good evening!", "Night owl learner!", "One more game?"]
    import random
    return random.choice(msgs)


# Car tier display info
CAR_TIERS = [
    {"emoji": "\U0001F3CE\uFE0F", "name": "Go-kart"},     # 0 coins
    {"emoji": "\U0001F697", "name": "Sedan"},               # 5 coins
    {"emoji": "\U0001F3CE\uFE0F", "name": "Sports Car"},   # 15 coins
    {"emoji": "\U0001F3C1", "name": "Race Car"},             # 30 coins
    {"emoji": "\U0001F680", "name": "F1 Car"},               # 50 coins
]


@router.get("/")
def game_page(request: Request, db: Session = Depends(get_db)):
    """Game selector page — pick Chinese, Math, or Logic."""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    user.reset_daily_if_needed()
    db.commit()

    from app.config import get_settings
    settings = get_settings()
    limit = settings.max_sessions_per_day
    remaining = max(0, limit - user.sessions_today) if limit > 0 else -1  # -1 = unlimited
    game_error = request.session.pop("game_error", None)

    today_points = _get_today_points(db, user.id)
    motivational = _get_motivational_message(user.streak)

    # Car tier info
    car_info = CAR_TIERS[min(user.car_level, len(CAR_TIERS) - 1)]
    next_tier_idx = min(user.car_level + 1, len(settings.car_tier_thresholds) - 1)
    coins_to_next_car = max(0, settings.car_tier_thresholds[next_tier_idx] - user.coins) if user.car_level < len(CAR_TIERS) - 1 else 0

    # Achievement count
    from app.services.achievements import get_earned_badges
    badge_count = len(get_earned_badges(db, user.id))

    # Quest progress
    from app.models.quest import QuestProgress
    qp = db.query(QuestProgress).filter_by(user_id=user.id).first()
    quest_info = None
    if qp:
        quest_info = {
            "season": qp.season,
            "stage": qp.stage,
            "sessions_in_stage": qp.sessions_in_stage,
            "sessions_needed": settings.quest_sessions_per_stage,
        }

    return templates.TemplateResponse("game_selector.html", {
        "request": request,
        "user": user,
        "remaining_sessions": remaining,
        "can_play": can_start_session(user),
        "game_error": game_error,
        "today_points": today_points,
        "motivational": motivational,
        "car_info": car_info,
        "coins_to_next_car": coins_to_next_car,
        "badge_count": badge_count,
        "quest_info": quest_info,
        "car_tiers": CAR_TIERS,
    })


@router.get("/chinese")
def chinese_game(request: Request, db: Session = Depends(get_db)):
    return _start_game_session(request, db, "chinese")


@router.get("/math")
def math_game(request: Request, db: Session = Depends(get_db)):
    return _start_game_session(request, db, "math")


@router.get("/logic")
def logic_game(request: Request, db: Session = Depends(get_db)):
    return _start_game_session(request, db, "logic")


@router.get("/english")
def english_game(request: Request, db: Session = Depends(get_db)):
    return _start_game_session(request, db, "english")


class AnswerRequest(BaseModel):
    question_id: int
    selected_answer: str


@router.post("/answer")
def answer_question(
    request: Request,
    body: AnswerRequest,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    try:
        result = submit_answer(db, user, body.question_id, body.selected_answer)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    return JSONResponse(result)


@router.post("/complete/{session_id}")
def complete(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    try:
        result = complete_session(db, user, session_id)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    return JSONResponse(result)


@router.get("/session-complete/{session_id}")
def session_complete_page(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    session = db.query(GameSession).filter_by(id=session_id, user_id=user.id).first()
    if not session:
        return RedirectResponse(url="/game/", status_code=303)
    if not session.completed_at:
        return RedirectResponse(url="/game/", status_code=303)

    from app.config import get_settings
    settings = get_settings()
    total_questions = len(session.questions)
    accuracy = round(session.total_correct / total_questions * 100) if total_questions else 0
    is_perfect = session.total_correct == total_questions
    stars_mod = user.stars % settings.coins_per_stars
    stars_progress_pct = round(stars_mod / settings.coins_per_stars * 100)
    car_info = CAR_TIERS[min(user.car_level, len(CAR_TIERS) - 1)]

    return templates.TemplateResponse(resolve_theme_template(user.theme, "session_complete.html"), {
        "request": request,
        "user": user,
        "session": session,
        "can_play_again": can_start_session(user),
        "total_questions": total_questions,
        "accuracy": accuracy,
        "is_perfect": is_perfect,
        "stars_progress_pct": stars_progress_pct,
        "stars_to_next_coin": settings.coins_per_stars - stars_mod,
        "car_info": car_info,
    })


@router.post("/buy-streak-freeze")
def buy_streak_freeze_route(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    from app.services.rewards import buy_streak_freeze
    success = buy_streak_freeze(db, user)
    if not success:
        return JSONResponse({"error": "Not enough coins"}, status_code=400)
    db.commit()
    return JSONResponse({
        "success": True,
        "coins": user.coins,
        "streak_freezes": user.streak_freezes,
    })


@router.post("/start-question/{question_id}")
def start_question(question_id: int, request: Request, db: Session = Depends(get_db)):
    """Record when a question is first shown (for speed bonus)."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    from datetime import datetime, timezone
    q = db.query(SessionQuestion).filter_by(id=question_id).first()
    if q and not q.started_at:
        q.started_at = datetime.now(timezone.utc)
        db.commit()
    return JSONResponse({"ok": True})


@router.get("/achievements")
def achievements_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    from app.services.achievements import BADGES, get_earned_badges
    earned = get_earned_badges(db, user.id)

    badges_list = []
    for key, badge in BADGES.items():
        badges_list.append({
            "key": key,
            "name": badge["name"],
            "description": badge["description"],
            "emoji": badge["emoji"],
            "earned": key in earned,
        })

    return templates.TemplateResponse("achievements.html", {
        "request": request,
        "user": user,
        "badges": badges_list,
        "earned_count": len(earned),
        "total_count": len(BADGES),
    })


@router.get("/quest")
def quest_map_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    from app.models.quest import QuestProgress
    from app.config import get_settings
    settings = get_settings()

    qp = db.query(QuestProgress).filter_by(user_id=user.id).first()
    if not qp:
        qp = QuestProgress(user_id=user.id, season=1, stage=1, sessions_in_stage=0)
        db.add(qp)
        db.commit()

    stages = []
    for i in range(1, settings.quest_stages_per_season + 1):
        if i < qp.stage:
            status = "complete"
        elif i == qp.stage:
            status = "current"
        else:
            status = "locked"
        stages.append({"number": i, "status": status})

    return templates.TemplateResponse("quest_map.html", {
        "request": request,
        "user": user,
        "quest": qp,
        "stages": stages,
        "sessions_needed": settings.quest_sessions_per_stage,
    })


_tts_cache: dict[str, bytes] = {}

# Voice mapping: natural-sounding Microsoft Neural voices
_VOICE_MAP = {
    "zh-CN": "zh-CN-XiaoxiaoNeural",   # warm, friendly female
    "zh":    "zh-CN-XiaoxiaoNeural",
    "en-US": "en-US-AvaNeural",          # clear, warm native English
    "en":    "en-US-AvaNeural",
}


def _clean_tts_text(text: str) -> str:
    """Strip emojis, underscores, and other non-speakable characters from TTS input."""
    import re
    # Remove emojis and symbol blocks
    cleaned = re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE00-\uFE0F\u200D\u20E3\U000E0020-\U000E007F]', '', text)
    # Remove underscores (fill-in-blank placeholders)
    cleaned = re.sub(r'_+', '', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


@router.get("/tts")
async def tts_proxy(text: str = Query(..., max_length=50), lang: str = Query("zh-CN", max_length=10)):
    """Generate TTS audio using Microsoft Edge neural voices via edge-tts."""
    import edge_tts

    text = _clean_tts_text(text)
    if not text:
        return Response(content=b"", media_type="audio/mpeg", status_code=204)

    cache_key = f"{lang}:{text}"
    if cache_key in _tts_cache:
        return Response(
            content=_tts_cache[cache_key],
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    voice = _VOICE_MAP.get(lang, _VOICE_MAP.get(lang.split("-")[0], "zh-CN-XiaoxiaoNeural"))
    # Slightly slower rate for kids, slightly higher pitch for warmth
    rate = "-15%" if lang.startswith("zh") else "-10%"
    pitch = "+5Hz" if lang.startswith("zh") else "+0Hz"

    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        audio_bytes = b""
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        if len(audio_bytes) > 100:
            # Cache (cap at 2000 entries to prevent memory bloat)
            if len(_tts_cache) < 2000:
                _tts_cache[cache_key] = audio_bytes
            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        pass

    # Return empty audio on failure
    return Response(content=b"", media_type="audio/mpeg", status_code=204)
