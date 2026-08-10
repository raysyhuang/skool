# Skool - Chinese Character Learning Game

A daily micro-learning app that teaches Chinese characters to kids through interactive games. Built as an iPad-first web app with age-appropriate modes for different learners.

## Features

- **540 Chinese words & phrases** — characters, compound words, idioms, and more
- **Age-appropriate game modes:**
  - **Daniel (age 4):** Picture matching — see a character, tap the correct image
  - **Ellie (age 9):** Multiple modes — character-to-meaning, fill-in-the-blank, pinyin-to-character, true/false
- **Spaced repetition** — characters you struggle with appear more often
- **Points & rewards** — earn stars, coins, and real-world rewards
- **Natural Chinese TTS** — Google Translate pronunciation via server proxy
- **Real background music** — royalty-free kids tracks from Mixkit
- **Dynamic themes** — 6 randomized CSS backgrounds per session
- **219 custom SVG icons** — hand-crafted illustrations for concrete nouns
- **iPad-first design** — 60px+ touch targets, portrait & landscape support

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Jinja2
- **Frontend:** Vanilla JS, CSS animations, Web Audio API for sound effects
- **Database:** SQLite (local) / PostgreSQL (Heroku)
- **Auth:** session cookie. Kids log in by tapping their avatar — no PIN,
  because a 4-year-old can't manage one. The 4-digit PIN gates the parent
  dashboard only.
- **TTS:** Google Translate proxy for natural Chinese pronunciation, with a
  Web Speech API fallback when autoplay is blocked

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database (users, characters, and learning topics)
python -m app.seed.seed_db

# Re-import learning topics only (idempotent — safe on a live database)
python -m app.seed.seed_taxonomy

# Upgrade an existing database's schema — only for a database Alembic already
# tracks. One built by seed_db/create_all has no alembic_version row, and the
# initial migration then fails on tables that already exist. Those databases
# self-upgrade at app startup instead (see _MIGRATIONS in app/main.py).
alembic upgrade head

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v
```

## Default Users

| User | PIN | Theme | Age Group |
|------|-----|-------|-----------|
| Daniel | 0000 | Racing | 4yo — picture matching only |
| Ellie | 1111 | Pony | 9yo — text & character modes |
| Parent | 8888 | Dashboard | Progress, drills, dinner prompts |

## Learning Topics

Math and English questions are chosen by *topic* rather than at random, using
the [Marble Skill Taxonomy](https://github.com/lauramionel/os-taxonomy) — 1,325
micro-topics for ages 4-10 plus the prerequisite graph between them. Each topic
carries its own SM-2 schedule, so the app tracks what a child has actually
mastered and introduces new topics only once their prerequisites are in place.

90 of those topics are **playable** — an existing question generator covers
them (`app/seed/taxonomy/topic_modes.json`). The rest are reference-only and
power the parent dashboard's "Ask at Dinner" prompts, which reach into science,
history, and life skills the app can't quiz.

See `NOTICE` for the upstream licences (ODbL 1.0 / CC BY-SA 4.0).

## Game Rules

- 5 questions per session, max 2 sessions per day
- Spaced repetition: SM-2 (easiness factor, interval, next review date).
  The 0-5 mastery score shown in the dashboard is derived from the SM-2
  repetition count, not incremented directly.
- Points: +2 correct, +5 daily bonus, +streak bonus
- Rewards: points -> stars (1:1) -> coins (10:1) -> RMB (10 coins = 20 yuan)

## Deployment

Deployed on Heroku with PostgreSQL:

```bash
git push heroku main
```

## License

Private project for family use. Background music tracks are royalty-free from [Mixkit](https://mixkit.co/) under the Mixkit License.
