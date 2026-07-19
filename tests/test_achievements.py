import json
from datetime import datetime, timezone

from app.config import get_settings
from app.services.achievements import BADGES, check_badges
from app.services.session_engine import create_session, submit_answer, complete_session


def _complete_perfect_session(db, user):
    session = create_session(db, user)
    for q in session.questions:
        submit_answer(db, user, q.id, q.correct_answer)
    return session, complete_session(db, user, session.id)


def test_first_session_and_perfect_badges(db, sample_user, sample_characters):
    _, summary = _complete_perfect_session(db, sample_user)
    keys = {b["key"] for b in summary["new_badges"]}
    assert "first_session" in keys
    assert "perfect_5" in keys


def test_speed_demon_survives_mixed_naive_aware_datetimes(db, sample_user, sample_characters):
    session = create_session(db, sample_user)
    for q in session.questions:
        submit_answer(db, sample_user, q.id, q.correct_answer)
        # Simulate the naive/aware mix PostgreSQL can produce
        q.started_at = datetime.now(timezone.utc)
        q.answered_at = datetime.utcnow()
    db.commit()
    summary = complete_session(db, sample_user, session.id)
    assert "speed_demon" in {b["key"] for b in summary["new_badges"]}


def test_century_awarded_at_100_stars_earned(db, sample_user, sample_characters):
    settings = get_settings()
    sample_user.points = 100 // settings.stars_per_point
    db.commit()
    _, summary = _complete_perfect_session(db, sample_user)
    assert "century" in {b["key"] for b in summary["new_badges"]}


def test_collector_badges_match_car_levels(db, sample_user, sample_characters):
    sample_user.car_level = 1  # Sedan (5 coins)
    db.commit()
    _, summary = _complete_perfect_session(db, sample_user)
    keys = {b["key"] for b in summary["new_badges"]}
    assert "collector_5" in keys
    assert "collector_15" not in keys

    sample_user.car_level = 2  # Sports Car (15 coins)
    db.commit()
    _, summary = _complete_perfect_session(db, sample_user)
    assert "collector_15" in {b["key"] for b in summary["new_badges"]}


def test_badges_not_awarded_twice(db, sample_user, sample_characters):
    _, first = _complete_perfect_session(db, sample_user)
    assert "first_session" in {b["key"] for b in first["new_badges"]}
    _, second = _complete_perfect_session(db, sample_user)
    assert "first_session" not in {b["key"] for b in second["new_badges"]}
