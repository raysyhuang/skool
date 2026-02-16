from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import validate_pin, get_child_users

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    users = get_child_users(db)
    error = request.query_params.get("error", "")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "users": users,
        "error": error,
    })


@router.post("/login")
def login(
    request: Request,
    user_id: int = Form(...),
    pin: str = Form(...),
    db: Session = Depends(get_db),
):
    user = validate_pin(db, user_id, pin)
    if not user:
        return RedirectResponse(url="/login?error=Wrong+PIN", status_code=303)

    response = RedirectResponse(url="/game/", status_code=303)
    request.session["user_id"] = user.id
    request.session["user_name"] = user.name
    request.session["theme"] = user.theme
    return response


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
