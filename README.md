# Skool - Chinese Character Learning Game

A daily micro-learning app that teaches Chinese characters to kids through interactive games. Built as an iPad-first web app with age-appropriate modes for different learners.

## Features

- **500 Chinese words & phrases** — characters, compound words, idioms, and more
- **Age-appropriate game modes:**
  - **Daniel (age 4):** Picture matching — see a character, tap the correct image
  - **Ellie (age 8):** Multiple modes — character-to-meaning, fill-in-the-blank, pinyin-to-character, true/false
- **Spaced repetition** — characters you struggle with appear more often
- **Points & rewards** — earn stars, coins, and real-world rewards
- **Natural Chinese TTS** — Google Translate pronunciation via server proxy
- **Real background music** — royalty-free kids tracks from Mixkit
- **Dynamic themes** — 6 randomized CSS backgrounds per session
- **220+ custom SVG icons** — hand-crafted illustrations for concrete nouns
- **iPad-first design** — 60px+ touch targets, portrait & landscape support

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Jinja2
- **Frontend:** Vanilla JS, CSS animations, Web Audio API for sound effects
- **Database:** SQLite (local) / PostgreSQL (Heroku)
- **Auth:** 4-digit PIN + session cookie
- **TTS:** Google Translate proxy for natural Chinese pronunciation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database
python -m app.seed.seed_db

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v
```

## Default Users

| User | PIN | Theme | Age Group |
|------|-----|-------|-----------|
| Daniel | 0000 | Racing | 4yo — picture matching only |
| Ellie | 1111 | Pony | 8yo — text & character modes |
| Parent | 8888 | Dashboard | Admin (Phase 2) |

## Game Rules

- 5 questions per session, max 2 sessions per day
- Spaced repetition: mastery 0-5 (+1 correct, -1 wrong)
- Points: +2 correct, +5 daily bonus, +streak bonus
- Rewards: points -> stars (1:1) -> coins (10:1) -> RMB (10 coins = 20 yuan)

## Deployment

Deployed on Heroku with PostgreSQL:

```bash
git push heroku main
```

## License

Private project for family use. Background music tracks are royalty-free from [Mixkit](https://mixkit.co/) under the Mixkit License.
