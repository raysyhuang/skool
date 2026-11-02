from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./skool.db"

    @field_validator("database_url")
    @classmethod
    def _normalise_postgres_url(cls, url: str) -> str:
        # Heroku sets postgres://, which SQLAlchemy rejects; and SQLAlchemy 2.1
        # made psycopg (v3) the default driver, so name psycopg2 (what we ship)
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg2://" + url[len(prefix):]
        return url

    # Session
    secret_key: str = "change-me-in-production"
    session_cookie_name: str = "skool_session"
    debug: bool = False  # Set to True for local dev

    # Game rules
    questions_per_session: int = 5
    max_sessions_per_day: int = 2  # 0 = unlimited; override via MAX_SESSIONS_PER_DAY
    distractors_per_question: int = 2  # + 1 correct = 3 options

    # Scoring
    points_correct: int = 2
    points_wrong: int = 0
    points_retry: int = 1  # right on a later attempt: some credit, no "correct" count
    daily_bonus: int = 5
    streak_bonus_multiplier: int = 1  # extra points per streak day

    # Reward conversion
    stars_per_point: int = 1       # 1 point = 1 star
    coins_per_stars: int = 10      # 10 stars = 1 coin
    rmb_per_coins: int = 10        # 10 coins = 20 RMB
    rmb_payout: float = 20.0

    # Variable rewards
    perfect_bonus_multiplier: int = 2   # 2x points for perfect session
    lucky_star_chance: float = 0.10     # 10% chance of lucky star
    lucky_star_multiplier: int = 3      # 3x multiplier on lucky star
    speed_bonus_threshold_seconds: int = 5  # answer within 5s for +1 bonus

    # Car evolution tiers (coins required)
    car_tier_thresholds: list[int] = [0, 5, 15, 30, 50]

    # Quest / season
    quest_stages_per_season: int = 5
    quest_sessions_per_stage: int = 3
    quest_stage_bonus_coins: int = 1
    quest_season_bonus_coins: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
