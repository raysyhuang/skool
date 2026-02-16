from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routes import auth, game


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except Exception:
            pass  # Tables already exist (created by seed script)
        yield

    app = FastAPI(title="Skool - Chinese Character Learning", lifespan=lifespan)

    # Session middleware for cookie-based auth
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    # Static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Routes
    app.include_router(auth.router)
    app.include_router(game.router)

    # Root redirect
    @app.get("/")
    def root(request: Request):
        if request.session.get("user_id"):
            return RedirectResponse(url="/game/", status_code=303)
        return RedirectResponse(url="/login", status_code=303)

    return app


app = create_app()
