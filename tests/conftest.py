import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import *  # noqa: register all models
from app.models.user import User
from app.models.character import Character
from app.main import create_app


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_user(db):
    user = User(name="Test Kid", pin="0000", age=4, theme="racing", role="child")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def sample_characters(db):
    chars = []
    for i, (char, pinyin, meaning) in enumerate([
        ("大", "dà", "big"),
        ("小", "xiǎo", "small"),
        ("人", "rén", "person"),
        ("口", "kǒu", "mouth"),
        ("手", "shǒu", "hand"),
        ("日", "rì", "sun"),
        ("月", "yuè", "moon"),
        ("水", "shuǐ", "water"),
        ("火", "huǒ", "fire"),
        ("山", "shān", "mountain"),
    ]):
        c = Character(
            character=char,
            pinyin=pinyin,
            meaning=meaning,
            difficulty=1,
            tags="test",
            image_url=f"/static/images/chars/{meaning}.svg",
            target_users="all",
        )
        db.add(c)
        chars.append(c)
    db.commit()
    return chars
