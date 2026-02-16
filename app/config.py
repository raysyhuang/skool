from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./skool.db"

    # Session
    secret_key: str = "change-me-in-production"
    session_cookie_name: str = "skool_session"

    # Game rules
    questions_per_session: int = 5
    max_sessions_per_day: int = 0  # 0 = unlimited
    distractors_per_question: int = 2  # + 1 correct = 3 options

    # Scoring
    points_correct: int = 2
    points_wrong: int = 0
    daily_bonus: int = 5
    streak_bonus_multiplier: int = 1  # extra points per streak day

    # Reward conversion
    stars_per_point: int = 1       # 1 point = 1 star
    coins_per_stars: int = 10      # 10 stars = 1 coin
    rmb_per_coins: int = 10        # 10 coins = 20 RMB
    rmb_payout: float = 20.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
