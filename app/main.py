from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routes import auth, game
from app.routes import dashboard as dashboard_routes
from app.routes import store as store_routes
from app.routes import story as story_routes


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine, checkfirst=True)
        yield

    app = FastAPI(title="Skool - Chinese Character Learning", lifespan=lifespan)

    # Session middleware for cookie-based auth
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie_name,
    )

    # Static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Routes
    app.include_router(auth.router)
    app.include_router(game.router)
    app.include_router(dashboard_routes.router)
    app.include_router(store_routes.router)
    app.include_router(story_routes.router)

    # Service worker must be served from root scope
    @app.get("/sw.js")
    def service_worker():
        return FileResponse(
            Path("static/sw.js"),
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )

    # Root redirect
    @app.get("/")
    def root(request: Request):
        if request.session.get("user_id"):
            return RedirectResponse(url="/game/", status_code=303)
        return RedirectResponse(url="/login", status_code=303)

    return app


app = create_app()
