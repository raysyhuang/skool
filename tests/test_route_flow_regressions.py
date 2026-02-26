import json
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_db
from app.main import create_app
from app.models.character import Character
from app.models.session import GameSession
from app.models.user import User


def _build_client(
    with_characters: bool, age: int = 4, theme: str = "racing"
) -> tuple[TestClient, sessionmaker, int]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    user = User(name="Flow Kid", pin="0000", age=age, theme=theme, role="child")
    db.add(user)
    if with_characters:
        db.add_all([
            Character(character="大", pinyin="dà", meaning="big", difficulty=1, image_url="/static/images/chars/big.svg", target_users="all"),
            Character(character="小", pinyin="xiǎo", meaning="small", difficulty=1, image_url="/static/images/chars/small.svg", target_users="all"),
            Character(character="人", pinyin="rén", meaning="person", difficulty=1, image_url="/static/images/chars/person.svg", target_users="all"),
            Character(character="手", pinyin="shǒu", meaning="hand", difficulty=1, image_url="/static/images/chars/hand.svg", target_users="all"),
            Character(character="水", pinyin="shuǐ", meaning="water", difficulty=1, image_url="/static/images/chars/water.svg", target_users="all"),
        ])
    db.commit()
    user_id = user.id
    db.close()

    app = create_app()

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    return client, SessionLocal, user_id


def _play_full_game(client: TestClient, user_id: int, game_type: str) -> dict:
    """Login, start a game, answer all 5 questions correctly, and complete the session.

    Returns the completion response JSON.
    """
    # Login
    client.post("/login", data={"user_id": user_id}, follow_redirects=False)

    # Start game
    resp = client.get(f"/game/{game_type}")
    assert resp.status_code == 200, f"Game start failed: {resp.status_code}"

    html = resp.text

    # Extract questions and session ID from the rendered HTML
    q_match = re.search(r"window\.questionsData\s*=\s*(\[.*?\]);", html, re.DOTALL)
    s_match = re.search(r"window\.sessionId\s*=\s*(\d+);", html)
    assert q_match, "Could not find questionsData in HTML"
    assert s_match, "Could not find sessionId in HTML"

    questions = json.loads(q_match.group(1))
    session_id = int(s_match.group(1))

    assert len(questions) == 5, f"Expected 5 questions, got {len(questions)}"

    # Answer all questions correctly
    for q in questions:
        answer_resp = client.post(
            "/game/answer",
            json={"question_id": q["id"], "selected_answer": q["correct_answer"]},
        )
        assert answer_resp.status_code == 200, f"Answer failed: {answer_resp.text}"
        result = answer_resp.json()
        assert result["is_correct"] is True

    # Complete session
    complete_resp = client.post(f"/game/complete/{session_id}")
    assert complete_resp.status_code == 200, f"Complete failed: {complete_resp.text}"

    return complete_resp.json()


# ---------------------------------------------------------------------------
# Existing regression tests
# ---------------------------------------------------------------------------


def test_game_start_without_characters_redirects_instead_of_500():
    client, _, user_id = _build_client(with_characters=False)
    client.post("/login", data={"user_id": user_id}, follow_redirects=False)

    response = client.get("/game/chinese", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/game/"


def test_session_complete_page_requires_completed_session():
    client, SessionLocal, user_id = _build_client(with_characters=True)
    client.post("/login", data={"user_id": user_id}, follow_redirects=False)
    client.get("/game/chinese")

    db = SessionLocal()
    session = db.query(GameSession).first()
    session_id = session.id
    db.close()

    response = client.get(f"/game/session-complete/{session_id}", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/game/"


# ---------------------------------------------------------------------------
# Full game flow integration tests
# ---------------------------------------------------------------------------


def test_full_chinese_game_flow():
    client, _, user_id = _build_client(with_characters=True)
    result = _play_full_game(client, user_id, "chinese")

    assert result["total_correct"] == 5
    assert result["points_earned"] > 0


def test_full_math_game_flow():
    client, _, user_id = _build_client(with_characters=False)
    result = _play_full_game(client, user_id, "math")

    assert result["total_correct"] == 5
    assert result["points_earned"] > 0


def test_full_logic_game_flow():
    client, _, user_id = _build_client(with_characters=False)
    result = _play_full_game(client, user_id, "logic")

    assert result["total_correct"] == 5
    assert result["points_earned"] > 0


def test_session_complete_page_after_completion():
    client, _, user_id = _build_client(with_characters=False)
    result = _play_full_game(client, user_id, "math")
    session_id = result["session_id"]

    resp = client.get(f"/game/session-complete/{session_id}")
    assert resp.status_code == 200


def test_wrong_answer_then_retry():
    client, _, user_id = _build_client(with_characters=False)
    client.post("/login", data={"user_id": user_id}, follow_redirects=False)

    resp = client.get("/game/math")
    assert resp.status_code == 200

    html = resp.text
    q_match = re.search(r"window\.questionsData\s*=\s*(\[.*?\]);", html, re.DOTALL)
    questions = json.loads(q_match.group(1))
    first_q = questions[0]

    # Submit a wrong answer
    wrong_option = next(
        opt for opt in first_q["options"] if opt != first_q["correct_answer"]
    )
    wrong_resp = client.post(
        "/game/answer",
        json={"question_id": first_q["id"], "selected_answer": wrong_option},
    )
    assert wrong_resp.status_code == 200
    assert wrong_resp.json()["is_correct"] is False

    # Retry with correct answer
    correct_resp = client.post(
        "/game/answer",
        json={"question_id": first_q["id"], "selected_answer": first_q["correct_answer"]},
    )
    assert correct_resp.status_code == 200
    assert correct_resp.json()["is_correct"] is True


def test_answer_without_login_returns_401():
    client, _, _ = _build_client(with_characters=False)

    resp = client.post(
        "/game/answer",
        json={"question_id": 1, "selected_answer": "x"},
    )
    assert resp.status_code == 401


def test_complete_without_login_returns_401():
    client, _, _ = _build_client(with_characters=False)

    resp = client.post("/game/complete/1")
    assert resp.status_code == 401


def test_logout_clears_session():
    client, _, user_id = _build_client(with_characters=False)
    client.post("/login", data={"user_id": user_id}, follow_redirects=False)

    # Verify logged in — game selector is accessible
    resp = client.get("/game/", follow_redirects=False)
    assert resp.status_code == 200

    # Logout
    client.get("/logout", follow_redirects=False)

    # Now game selector should redirect to login
    resp = client.get("/game/", follow_redirects=False)
    assert resp.status_code == 303
    assert "/login" in resp.headers["location"]


def test_root_redirects_based_on_login():
    client, _, user_id = _build_client(with_characters=False)

    # Unauthenticated → login
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert "/login" in resp.headers["location"]

    # Authenticated → game selector
    client.post("/login", data={"user_id": user_id}, follow_redirects=False)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert "/game/" in resp.headers["location"]


def test_older_kid_math_game_flow():
    client, _, user_id = _build_client(with_characters=False, age=8)
    result = _play_full_game(client, user_id, "math")

    assert result["total_correct"] == 5
    assert result["points_earned"] > 0


def test_older_kid_logic_game_flow():
    client, _, user_id = _build_client(with_characters=False, age=8)
    result = _play_full_game(client, user_id, "logic")

    assert result["total_correct"] == 5
    assert result["points_earned"] > 0
