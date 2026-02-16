from pydantic import BaseModel
from typing import Optional


class CharacterCreate(BaseModel):
    character: str
    pinyin: str
    meaning: str
    difficulty: int
    tags: Optional[str] = None
    image_url: Optional[str] = None
    sentence_template: Optional[str] = None
    explanation: Optional[str] = None
    target_users: str = "all"
