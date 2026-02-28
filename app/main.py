from contextlib import asynccontextmanager
import logging

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routes import auth, game
from app.routes import dashboard as dashboard_routes
from app.routes import store as store_routes
from app.routes import story as story_routes

logger = logging.getLogger(__name__)

_templates = Jinja2Templates(directory="templates")


def _run_migrations(engine_instance):
    """Add missing columns to existing tables.

    create_all() only creates new tables; it won't ALTER existing ones.
    This function adds columns idempotently using dialect-appropriate SQL.
    """
    _MIGRATIONS = [
        # (table, column, SQL type, default)
        ("users", "streak_freezes", "INTEGER", "0"),
        ("users", "best_streak", "INTEGER", "0"),
        ("users", "perfect_sessions", "INTEGER", "0"),
        ("users", "total_sessions_completed", "INTEGER", "0"),
        ("users", "car_level", "INTEGER", "0"),
        ("users", "equipped_car_skin", "VARCHAR", None),
        ("users", "equipped_background", "VARCHAR", None),
        ("users", "equipped_trail", "VARCHAR", None),
        ("session_questions", "started_at", "TIMESTAMP", None),
        # SM-2 spaced repetition columns
        ("user_character_progress", "easiness_factor", "REAL", "2.5"),
        ("user_character_progress", "sm2_interval", "INTEGER", "0"),
        ("user_character_progress", "sm2_repetitions", "INTEGER", "0"),
        ("user_character_progress", "next_review_date", "DATE", None),
    ]

    dialect = engine_instance.dialect.name  # "postgresql" or "sqlite"
    with engine_instance.begin() as conn:
        for table, column, col_type, default in _MIGRATIONS:
            default_clause = f" DEFAULT {default}" if default is not None else ""
            if dialect == "postgresql":
                stmt = (
                    f"ALTER TABLE {table} "
                    f"ADD COLUMN IF NOT EXISTS {column} {col_type}{default_clause}"
                )
            else:
                # SQLite: no IF NOT EXISTS for ADD COLUMN; catch error
                stmt = (
                    f"ALTER TABLE {table} "
                    f"ADD COLUMN {column} {col_type}{default_clause}"
                )
            try:
                conn.execute(text(stmt))
                logger.info("Migration applied: %s.%s", table, column)
            except Exception:
                # Column already exists — safe to ignore
                pass

        # One-time data fix: update Ellie's age from 8 to 9
        try:
            conn.execute(text(
                "UPDATE users SET age = 9 WHERE name = 'Ellie' AND age = 8"
            ))
        except Exception:
            pass


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine, checkfirst=True)
        _run_migrations(engine)
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

    # Offline fallback page
    @app.get("/offline")
    def offline_page(request: Request):
        return _templates.TemplateResponse("offline.html", {"request": request})

    # Root redirect
    @app.get("/")
    def root(request: Request):
        if request.session.get("user_id"):
            return RedirectResponse(url="/game/", status_code=303)
        return RedirectResponse(url="/login", status_code=303)

    # ── Global exception handlers ──

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        is_api = request.url.path.startswith("/api/") or request.url.path.startswith("/game/answer") or request.url.path.startswith("/game/complete") or "application/json" in request.headers.get("accept", "")
        if is_api:
            return JSONResponse({"error": exc.detail}, status_code=exc.status_code)
        if exc.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
            f"<h1>Oops! Something went wrong</h1>"
            f"<p style='font-size:18px;color:#636e72;'>{exc.detail}</p>"
            f"<a href='/game/' style='display:inline-block;margin-top:20px;padding:12px 24px;"
            f"background:#6c5ce7;color:#fff;border-radius:12px;text-decoration:none;font-size:18px;'>Go Home</a>"
            f"</body></html>",
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        is_api = request.url.path.startswith("/api/") or request.url.path.startswith("/game/answer") or request.url.path.startswith("/game/complete") or "application/json" in request.headers.get("accept", "")
        if is_api:
            return JSONResponse({"error": "Something went wrong"}, status_code=500)
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
            "<h1>Oops! Something went wrong</h1>"
            "<p style='font-size:18px;color:#636e72;'>Please try again.</p>"
            "<a href='/game/' style='display:inline-block;margin-top:20px;padding:12px 24px;"
            "background:#6c5ce7;color:#fff;border-radius:12px;text-decoration:none;font-size:18px;'>Go Home</a>"
            "</body></html>",
            status_code=500,
        )

    return app


app = create_app()
