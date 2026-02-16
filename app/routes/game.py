import json
import os
import urllib.parse
import httpx
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


def _build_questions_json(questions) -> list[dict]:
    """Build the questions data list for the frontend, including extra fields for new modes."""
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


@router.get("/")
def game_page(request: Request, db: Session = Depends(get_db)):
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

    # Create a new session
    try:
        session = create_session(db, user)
    except SessionLimitReached:
        return templates.TemplateResponse(resolve_theme_template(user.theme, "limit_reached.html"), {
            "request": request,
            "user": user,
        })

    # Get first question
    questions = session.questions
    first_q = questions[0]
    options = json.loads(first_q.options)

    return templates.TemplateResponse(resolve_theme_template(user.theme, "game.html"), {
        "request": request,
        "user": user,
        "session": session,
        "question": first_q,
        "character": first_q.character,
        "options": options,
        "question_number": first_q.question_number,
        "total_questions": len(questions),
        "questions_json": json.dumps(_build_questions_json(questions)),
    })


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

    return templates.TemplateResponse(resolve_theme_template(user.theme, "session_complete.html"), {
        "request": request,
        "user": user,
        "session": session,
        "can_play_again": can_start_session(user),
    })


@router.get("/tts")
async def tts_proxy(text: str = Query(..., max_length=50)):
    """Proxy Google Translate TTS to avoid browser CORS/blocking issues."""
    url = (
        "https://translate.google.com/translate_tts"
        f"?ie=UTF-8&tl=zh-CN&client=tw-ob&q={urllib.parse.quote(text)}"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://translate.google.com/",
            }, timeout=5.0)
        if resp.status_code == 200 and len(resp.content) > 100:
            return Response(
                content=resp.content,
                media_type="audio/mpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        pass
    # Return empty audio on failure
    return Response(content=b"", media_type="audio/mpeg", status_code=204)
