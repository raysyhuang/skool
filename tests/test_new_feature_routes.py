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
