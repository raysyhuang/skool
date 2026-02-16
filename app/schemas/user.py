from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    user_id: int
    pin: str


class UserStats(BaseModel):
    name: str
    theme: str
    points: int
    stars: int
    coins: int
    streak: int
    sessions_today: int
