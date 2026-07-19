# Skool — Chinese Character Learning App

## Project Overview
Daily micro-learning reinforcement engine for two kids:
- **Son (弟弟, age 4):** Racing car theme, picture matching only (pre-readers are age-gated to the Chinese game)
- **Daughter (姐姐, age 9):** Pony/unicorn theme (reskin of the racing engine via `app/themes.py` + `static/css/pony.css`), mixed question modes
- **Parent (爸爸):** Dashboard, PIN 8888

Auth: kids log in by tapping their avatar — deliberately no PIN (a
4-year-old can't manage one; the PIN gate protects the parent dashboard).

## Tech Stack
- **Backend:** FastAPI + SQLAlchemy + Jinja2
- **Frontend:** Vanilla JS, CSS animations, Web Speech API for TTS
- **Database:** SQLite (local) / PostgreSQL (Heroku)
- **Auth:** 4-digit PIN + session cookie

## Key Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database
python -m app.seed.seed_db

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Deploy to Heroku
git push heroku main
```

## Project Structure
- `app/models/` — SQLAlchemy models (User, Character, Progress, Session, Rewards)
- `app/services/` — Business logic (session engine, spaced repetition, rewards, question generation)
- `app/routes/` — FastAPI route handlers (auth, game)
- `app/seed/` — Seed data JSON + script
- `templates/` — Jinja2 templates organized by theme
- `static/` — CSS, JS, images
- `tests/` — pytest tests

## Game Rules
- 5 questions per session, max 2 sessions per day (override with the
  `MAX_SESSIONS_PER_DAY` env var; 0 = unlimited)
- Spaced repetition: SM-2 (mastery 0-5 derived for display)
- Points: +2 correct, +5 daily bonus, +streak bonus, lucky-star/speed bonuses
- Rewards: points → stars (1:1) → coins (10:1) → RMB (10 coins = ¥20)
- Car/pony tier progression is driven by `users.lifetime_coins`
  (never decremented), so store spending can't demote anyone
- `SECRET_KEY` must be set on Heroku (app refuses to boot with the
  default secret when `DYNO` is present)

## iPad-First Design
- All touch targets >= 60px
- No pinch-zoom, no horizontal scroll
- Web Speech API for Chinese TTS
- Portrait and landscape support
