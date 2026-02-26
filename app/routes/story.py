import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.progress import UserCharacterProgress
from app.services.story_generator import STORIES, get_available_stories

router = APIRouter(prefix="/game/stories")
templates = Jinja2Templates(directory="templates")


def _get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


@router.get("/")
def stories_list(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Calculate average mastery
    avg = (
        db.query(func.avg(UserCharacterProgress.mastery_score))
        .filter_by(user_id=user.id)
        .scalar()
    ) or 0

    stories = get_available_stories(float(avg))

    return templates.TemplateResponse("story_list.html", {
        "request": request,
        "user": user,
        "stories": stories,
    })


@router.get("/{story_id}")
def read_story(story_id: int, request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    story = None
    for s in STORIES:
        if s["id"] == story_id:
            story = s
            break

    if not story:
        return RedirectResponse(url="/game/stories/", status_code=303)

    return templates.TemplateResponse("story.html", {
        "request": request,
        "user": user,
        "story": story,
    })
