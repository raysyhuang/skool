"""Regressions for the quests / garage / journey routes and quest rewards."""
import json

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import create_app
from app.models import DailyQuest, UserDailyQuestProgress
from app.models.collectibles import CollectibleItem, JourneyNode, UserCollectible
from app.services.daily_quests import claim_quest_reward, update_quest_progress


def _client(db, user=None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app, base_url="https://testserver")  # cookies are https_only
    if user is not None:
        client.post("/login", data={"user_id": user.id}, follow_redirects=False)
    return client


def test_session_counts_toward_quests_before_quest_page_opened(db, sample_user):
    assert db.query(DailyQuest).count() == 0
    result = update_quest_progress(db, sample_user.id, "play_session", 1)
    assert result is not None and result["quest_type"] == "play_session"


def test_combo_and_streak_quests_complete_after_one_qualifying_session(db, sample_user):
    assert update_quest_progress(db, sample_user.id, "combo_master", 1) is not None
    assert update_quest_progress(db, sample_user.id, "streak_keeper", 1) is not None


def test_claim_star_quest_awards_points_once(db, sample_user):
    update_quest_progress(db, sample_user.id, "play_session", 1)
    progress = db.query(UserDailyQuestProgress).one()
    before = sample_user.points

    assert claim_quest_reward(db, sample_user.id, progress.id) is True
    assert sample_user.points == before + 5
    assert claim_quest_reward(db, sample_user.id, progress.id) is False
    assert sample_user.points == before + 5


def test_claim_coin_quest_counts_toward_lifetime_coins(db, sample_user):
    update_quest_progress(db, sample_user.id, "streak_keeper", 1)
    quest = db.query(DailyQuest).filter_by(quest_type="streak_keeper").one()
    progress = db.query(UserDailyQuestProgress).filter_by(quest_id=quest.id).one()

    assert claim_quest_reward(db, sample_user.id, progress.id) is True
    assert sample_user.coins == 1
    assert sample_user.lifetime_coins == 1


def test_claim_quest_route(db, sample_user):
    update_quest_progress(db, sample_user.id, "play_session", 1)
    progress = db.query(UserDailyQuestProgress).one()
    resp = _client(db, sample_user).post(f"/game/claim-quest/{progress.id}")
    assert resp.status_code == 200
    assert resp.json() == {"success": True}


def _item(db, key: str) -> CollectibleItem:
    item = CollectibleItem(item_type="car", item_key=key, name=key, price_coins=0)
    db.add(item)
    db.commit()
    return item


def test_equipping_unowned_item_is_refused_and_keeps_current_item(db, sample_user):
    owned, other = _item(db, "red"), _item(db, "blue")
    db.add(UserCollectible(user_id=sample_user.id, item_id=owned.id, equipped=True))
    db.commit()

    resp = _client(db, sample_user).post(f"/game/garage/equip/{other.id}")
    assert resp.status_code == 403
    mine = db.query(UserCollectible).filter_by(user_id=sample_user.id, item_id=owned.id).one()
    db.refresh(mine)
    assert mine.equipped is True


def test_journey_page_renders_with_unlocked_node(db, sample_user):
    db.add(JourneyNode(
        node_key="start", node_type="island", subject="math", order_index=0,
        title="Start", completion_requirement=json.dumps({"sessions": 5}),
    ))
    db.commit()
    resp = _client(db, sample_user).get("/game/journey")
    assert resp.status_code == 200


def test_placeholder_placement_routes_are_not_served(db, sample_user):
    client = _client(db, sample_user)
    assert client.post("/game/placement-test/math/start").status_code in (404, 405)
    assert client.get("/game/placement-test/1/next").status_code == 404


def test_startup_seeds_quest_definitions(db_engine):
    from sqlalchemy.orm import Session
    from app.main import _init_schema
    from app.services.daily_quests import DAILY_QUEST_POOL

    _init_schema(db_engine)
    _init_schema(db_engine)  # second worker / restart must not duplicate
    with Session(bind=db_engine) as s:
        assert s.query(DailyQuest).count() == len(DAILY_QUEST_POOL)


# ── Garage seeding, unlock requirements, home-screen wiring ──

def test_seed_collectibles_is_idempotent_and_seeds_rainbow_trail(db):
    from app.seed.seed_collectibles import COLLECTIBLES, seed_collectibles

    keys = [c["item_key"] for c in COLLECTIBLES]
    assert len(keys) == len(set(keys))
    assert seed_collectibles(db) == len(COLLECTIBLES)
    assert seed_collectibles(db) == 0
    assert db.query(CollectibleItem).count() == len(COLLECTIBLES)
    trail = db.query(CollectibleItem).filter_by(item_key="rainbow_trail").one()
    assert trail.item_type == "trail"


def test_seed_collectibles_upgrades_legacy_text_requirement(db):
    from app.seed.seed_collectibles import seed_collectibles

    db.add(CollectibleItem(item_type="car", item_key="golden_car", name="Golden",
                           price_coins=100, unlock_requirement="Reach 30-day streak"))
    db.commit()
    seed_collectibles(db)
    golden = db.query(CollectibleItem).filter_by(item_key="golden_car").one()
    assert json.loads(golden.unlock_requirement) == {"type": "streak", "value": 30}


def test_startup_seeds_collectibles(db_engine):
    from sqlalchemy.orm import Session
    from app.main import _init_schema
    from app.seed.seed_collectibles import COLLECTIBLES

    _init_schema(db_engine)
    _init_schema(db_engine)
    with Session(bind=db_engine) as s:
        assert s.query(CollectibleItem).count() == len(COLLECTIBLES)


def _locked_item(db, kind="streak", value=30, price=0) -> CollectibleItem:
    item = CollectibleItem(item_type="car", item_key=f"locked_{kind}", name="Locked",
                           price_coins=price,
                           unlock_requirement=json.dumps({"type": kind, "value": value}))
    db.add(item)
    db.commit()
    return item


def test_buying_locked_item_is_refused_until_requirement_met(db, sample_user):
    item = _locked_item(db, "streak", 30, price=5)
    sample_user.coins = 10
    sample_user.streak = 3
    db.commit()
    client = _client(db, sample_user)

    resp = client.post(f"/game/garage/buy/{item.id}")
    assert resp.status_code == 403
    assert resp.json()["requirement"] == "🔥 3/30"
    db.refresh(sample_user)
    assert sample_user.coins == 10
    assert db.query(UserCollectible).count() == 0

    sample_user.best_streak = 30
    db.commit()
    resp = client.post(f"/game/garage/buy/{item.id}")
    assert resp.status_code == 200 and resp.json()["success"] is True


def test_equipping_owned_but_locked_item_is_refused(db, sample_user):
    item = _locked_item(db, "perfect_sessions", 10)
    db.add(UserCollectible(user_id=sample_user.id, item_id=item.id, equipped=False))
    db.commit()
    client = _client(db, sample_user)
    assert client.post(f"/game/garage/equip/{item.id}").status_code == 403

    sample_user.perfect_sessions = 10
    db.commit()
    assert client.post(f"/game/garage/equip/{item.id}").status_code == 200


def test_accuracy_requirement_needs_enough_sessions(db, sample_user):
    from datetime import datetime, timezone
    from app.models.session import GameSession
    from app.routes.game_new_features import ACCURACY_MIN_SESSIONS, requirement_status

    raw = json.dumps({"type": "accuracy", "value": 95})
    now = datetime.now(timezone.utc)
    db.add(GameSession(user_id=sample_user.id, total_correct=5, total_wrong=0, completed_at=now))
    db.commit()
    assert requirement_status(db, sample_user, raw)["met"] is False

    for _ in range(ACCURACY_MIN_SESSIONS - 1):
        db.add(GameSession(user_id=sample_user.id, total_correct=5, total_wrong=0, completed_at=now))
    db.commit()
    assert requirement_status(db, sample_user, raw)["met"] is True


def test_unparseable_requirement_stays_locked(db, sample_user):
    from app.routes.game_new_features import requirement_status
    assert requirement_status(db, sample_user, "Do something")["met"] is False


def test_garage_page_shows_lock_progress(db, sample_user):
    from app.seed.seed_collectibles import seed_collectibles
    seed_collectibles(db)
    resp = _client(db, sample_user).get("/game/garage")
    assert resp.status_code == 200
    assert "🔥 0/30" in resp.text
    assert "Rainbow Trail" in resp.text


def test_home_screen_links_quests_and_garage_and_shows_progress(db, sample_user):
    from app.services.daily_quests import ensure_daily_quests
    ensure_daily_quests(db)
    update_quest_progress(db, sample_user.id, "play_session", 1)

    resp = _client(db, sample_user).get("/game/")
    assert resp.status_code == 200
    assert "/game/daily-quests" in resp.text
    assert "/game/garage" in resp.text
    assert 'id="questsBar"' in resp.text
    assert "display: none" not in resp.text.split('id="questsBar"')[1][:50]
    assert "quest-mini-claim" in resp.text  # completed, not yet claimed


def test_home_screen_shows_equipped_garage_item(db, sample_user):
    pet = CollectibleItem(item_type="pet", item_key="panda", name="Panda", emoji="🐼", price_coins=0)
    db.add(pet)
    db.commit()
    db.add(UserCollectible(user_id=sample_user.id, item_id=pet.id, equipped=True))
    db.commit()

    resp = _client(db, sample_user).get("/game/")
    assert 'class="equipped-strip"' in resp.text
    assert "🐼" in resp.text.split('class="equipped-strip"')[1][:300]


def test_home_screen_shows_equipped_store_car_skin(db, sample_user):
    from app.models.store import StoreItem
    db.add(StoreItem(key="car_tractor", name="Tractor", category="car_skin", price_coins=3, emoji="🚜"))
    sample_user.equipped_car_skin = "car_tractor"
    db.commit()

    resp = _client(db, sample_user).get("/game/")
    assert "🚜" in resp.text.split('class="equipped-strip"')[1][:300]


def test_session_complete_page_shows_quests_and_claim_link(db, sample_user):
    from datetime import datetime, timezone
    from app.models.session import GameSession
    from app.services.daily_quests import ensure_daily_quests

    ensure_daily_quests(db)
    session = GameSession(user_id=sample_user.id, total_correct=0, completed_at=datetime.now(timezone.utc))
    db.add(session)
    db.commit()
    update_quest_progress(db, sample_user.id, "play_session", 1)

    resp = _client(db, sample_user).get(f"/game/session-complete/{session.id}")
    assert resp.status_code == 200
    assert 'class="quests-row"' in resp.text
    assert 'id="questClaim"' in resp.text
