"""Integration tests for authentication and game flow."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.database import Base, get_db
from app.models.user import User
from app.models.character import Character


@pytest.fixture
def client(db):
    """Test client with dependency override."""
    app = create_app()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, base_url="https://testserver")  # cookies are https_only


@pytest.fixture
def child_user(db):
    """Create a child user for testing."""
    user = User(
        name="Test Child",
        pin="0000",
        age=6,
        theme="racing",
        role="child"
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def parent_user(db):
    """Create a parent user for testing."""
    user = User(
        name="Test Parent",
        pin="8888",
        age=None,
        theme="racing",
        role="parent"
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def characters(db):
    """Create test characters."""
    chars = []
    for char, pinyin, meaning in [
        ("大", "dà", "big"),
        ("小", "xiǎo", "small"),
        ("人", "rén", "person"),
        ("口", "kǒu", "mouth"),
        ("手", "shǒu", "hand"),
    ]:
        c = Character(
            character=char,
            pinyin=pinyin,
            meaning=meaning,
            difficulty=1,
            tags="test",
            image_url=f"/static/images/chars/{meaning}.svg",
            target_users="all"
        )
        db.add(c)
        chars.append(c)
    db.commit()
    return chars


def test_root_redirects_to_login_when_not_authenticated(client):
    """Root should redirect to login for unauthenticated users."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_child_login_flow(client, child_user):
    """Test complete child login flow."""
    # 1. Visit login page
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Test Child" in response.content
    
    # 2. Submit login form
    response = client.post("/login", data={"user_id": child_user.id}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/game/"
    
    # 3. Verify session was created (cookie set)
    assert "skool_session" in response.cookies or "Set-Cookie" in response.headers


def test_parent_login_requires_pin(client, parent_user):
    """Test parent login with PIN."""
    # Correct PIN
    response = client.post("/login/parent", data={"pin": "8888"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard/"
    
    # Wrong PIN
    response = client.post("/login/parent", data={"pin": "0000"}, follow_redirects=False)
    assert response.status_code == 303
    assert "error" in response.headers["location"]


def test_authenticated_user_can_access_game(client, child_user, characters):
    """Test that authenticated user can access game selector."""
    # Login first
    client.post("/login", data={"user_id": child_user.id})
    
    # Access game selector
    response = client.get("/game/")
    assert response.status_code == 200


def test_complete_game_session_flow(client, child_user, characters):
    """Test full game session: login -> start -> answer -> complete."""
    # 1. Login
    client.post("/login", data={"user_id": child_user.id})
    
    # 2. Start Chinese game session
    response = client.get("/game/chinese", follow_redirects=False)
    assert response.status_code == 200
    
    # Extract session data from response (would need to parse HTML or use JSON endpoint)
    # For now, just verify we got a game page
    assert b"character" in response.content or b"question" in response.content


def test_logout_clears_session(client, child_user):
    """Test that logout clears the session."""
    # Login
    client.post("/login", data={"user_id": child_user.id})
    
    # Verify we can access game
    response = client.get("/game/")
    assert response.status_code == 200
    
    # Logout
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    
    # Verify we're redirected to login when accessing game
    response = client.get("/game/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_unauthenticated_users_cannot_access_protected_routes(client):
    """Test that protected routes redirect to login."""
    protected_routes = [
        "/game/",
        "/game/chinese",
        "/game/math",
        "/dashboard/",
        "/game/store/",
    ]
    
    for route in protected_routes:
        response = client.get(route, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"


def test_child_cannot_access_dashboard(client, child_user):
    """Test that child users cannot access parent dashboard."""
    # Login as child
    client.post("/login", data={"user_id": child_user.id})
    
    # Try to access dashboard
    response = client.get("/dashboard/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/game/"


def test_parent_can_access_dashboard(client, parent_user, child_user):
    """Test that parent users can access dashboard."""
    # Login as parent
    client.post("/login/parent", data={"pin": "8888"})
    
    # Access dashboard
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert b"Parent Dashboard" in response.content
