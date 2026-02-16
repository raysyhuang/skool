# Skool — Chinese Character Learning App

## Project Overview
Daily micro-learning reinforcement engine for two kids:
- **Son (弟弟, age 4):** Racing car theme, picture matching, PIN 0000
- **Daughter (姐姐, age 8):** Pony theme (Phase 2), phrase builder, PIN 1111
- **Parent (爸爸):** Dashboard (Phase 2), PIN 8888

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
- 5 questions per session, max 2 sessions per day
- Spaced repetition: mastery 0-5 (+1 correct, -1 wrong)
- Points: +2 correct, +5 daily bonus, +streak bonus
- Rewards: points → stars (1:1) → coins (10:1) → RMB (10 coins = ¥20)

## iPad-First Design
- All touch targets >= 60px
- No pinch-zoom, no horizontal scroll
- Web Speech API for Chinese TTS
- Portrait and landscape support
