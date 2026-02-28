from contextlib import asynccontextmanager
import logging

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routes import auth, game
from app.routes import dashboard as dashboard_routes
from app.routes import store as store_routes
from app.routes import story as story_routes

logger = logging.getLogger(__name__)


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

    # Root redirect
    @app.get("/")
    def root(request: Request):
        if request.session.get("user_id"):
            return RedirectResponse(url="/game/", status_code=303)
        return RedirectResponse(url="/login", status_code=303)

    return app


app = create_app()
