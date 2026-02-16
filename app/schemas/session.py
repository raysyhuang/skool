from pydantic import BaseModel
from typing import Optional


class AnswerSubmission(BaseModel):
    question_id: int
    selected_answer: str


class QuestionData(BaseModel):
    question_id: int
    question_number: int
    character: str
    pinyin: str
    meaning: str
    image_url: Optional[str]
    options: list[str]  # 3 options (images or meanings)


class SessionSummary(BaseModel):
    session_id: int
    total_correct: int
    total_wrong: int
    points_earned: int
    streak: int
    total_points: int
    total_stars: int
    total_coins: int
