import json
from datetime import date, timedelta

import pytest

from app.models.user import User
from app.config import get_settings
from app.services.session_engine import (
    can_start_session,
    create_session,
    submit_answer,
    complete_session,
    SessionLimitReached,
)


def test_can_start_session_initially(db, sample_user, sample_characters):
    assert can_start_session(sample_user) is True


def test_create_session_generates_5_questions(db, sample_user, sample_characters):
    session = create_session(db, sample_user)
    assert len(session.questions) == 5


def test_create_session_increments_sessions_today(db, sample_user, sample_characters):
    create_session(db, sample_user)
    assert sample_user.sessions_today == 1


def test_unlimited_sessions_when_limit_zero(db, sample_user, sample_characters):
    """With max_sessions_per_day=0, unlimited sessions are allowed."""
    create_session(db, sample_user)
    create_session(db, sample_user)
    # Third session should work (no limit)
    s3 = create_session(db, sample_user)
    assert s3 is not None
    assert sample_user.sessions_today == 3


def test_submit_correct_answer(db, sample_user, sample_characters):
    session = create_session(db, sample_user)
    q = session.questions[0]
    result = submit_answer(db, sample_user, q.id, q.correct_answer)
    assert result["is_correct"] is True
    assert result["points_earned"] == 2


def test_submit_wrong_answer(db, sample_user, sample_characters):
    session = create_session(db, sample_user)
    q = session.questions[0]
    options = json.loads(q.options)
    wrong = [o for o in options if o != q.correct_answer][0]
    result = submit_answer(db, sample_user, q.id, wrong)
    assert result["is_correct"] is False
    assert result["points_earned"] == 0


def test_complete_session_returns_summary(db, sample_user, sample_characters):
    session = create_session(db, sample_user)
    # Answer all questions correctly
    for q in session.questions:
        submit_answer(db, sample_user, q.id, q.correct_answer)
    result = complete_session(db, sample_user, session.id)
    assert result["total_correct"] == 5
    assert result["session_id"] == session.id


def test_last_played_date_set(db, sample_user, sample_characters):
    create_session(db, sample_user)
    assert sample_user.last_played_date == date.today()


def test_complete_session_requires_all_questions_answered(db, sample_user, sample_characters):
    session = create_session(db, sample_user)
    with pytest.raises(ValueError, match="unanswered"):
        complete_session(db, sample_user, session.id)


def test_daily_bonus_applies_to_first_completed_session_even_if_multiple_started(db, sample_user, sample_characters):
    settings = get_settings()
    first = create_session(db, sample_user)
    create_session(db, sample_user)

    for q in first.questions:
        submit_answer(db, sample_user, q.id, q.correct_answer)

    result = complete_session(db, sample_user, first.id)
    base = len(first.questions) * settings.points_correct
    perfect_bonus = base * (settings.perfect_bonus_multiplier - 1)  # 2x perfect session
    streak_bonus = sample_user.streak * settings.streak_bonus_multiplier  # first play starts streak at 1
    expected = base + perfect_bonus + settings.daily_bonus + streak_bonus
    assert result["points_earned"] == expected


def test_retry_after_wrong_answer_awards_points_when_corrected(db, sample_user, sample_characters):
    settings = get_settings()
    session = create_session(db, sample_user)
    q = session.questions[0]
    options = json.loads(q.options)
    wrong = [o for o in options if o != q.correct_answer][0]

    first_try = submit_answer(db, sample_user, q.id, wrong)
    retry = submit_answer(db, sample_user, q.id, q.correct_answer)

    assert first_try["is_correct"] is False
    assert retry["is_correct"] is True
    assert retry["points_earned"] == settings.points_correct


def test_streak_increments_once_per_day(db, sample_user, sample_characters):
    sample_user.streak = 3
    sample_user.best_streak = 3
    sample_user.last_played_date = date.today() - timedelta(days=1)
    db.commit()

    create_session(db, sample_user)
    assert sample_user.streak == 4

    # Repeated daily resets and sessions on the same day must not inflate it
    sample_user.reset_daily_if_needed()
    create_session(db, sample_user)
    sample_user.reset_daily_if_needed()
    create_session(db, sample_user)
    assert sample_user.streak == 4
    assert sample_user.best_streak == 4


def test_streak_freeze_burns_one_per_gap(db, sample_user, sample_characters):
    sample_user.streak = 5
    sample_user.streak_freezes = 2
    sample_user.last_played_date = date.today() - timedelta(days=3)
    db.commit()

    create_session(db, sample_user)
    assert sample_user.streak_freezes == 1
    assert sample_user.streak == 5

    # Second session the same day burns nothing further
    create_session(db, sample_user)
    assert sample_user.streak_freezes == 1
    assert sample_user.streak == 5


def test_missed_day_without_freeze_restarts_streak_at_1(db, sample_user, sample_characters):
    sample_user.streak = 7
    sample_user.best_streak = 7
    sample_user.streak_freezes = 0
    sample_user.last_played_date = date.today() - timedelta(days=2)
    db.commit()

    create_session(db, sample_user)
    assert sample_user.streak == 1
    assert sample_user.best_streak == 7


def test_first_play_starts_streak_at_1(db, sample_user, sample_characters):
    assert sample_user.last_played_date is None
    create_session(db, sample_user)
    assert sample_user.streak == 1


def test_age_drives_character_pool_not_theme(db, sample_user, sample_characters):
    """A pre-reader only gets image-backed chars; a reader gets the full pool —
    regardless of which theme string is set on the user."""
    from app.models.character import Character
    from app.models.session import SessionQuestion

    imageless = Character(
        character="想", pinyin="xiǎng", meaning="to think", difficulty=2,
        tags="test", image_url=None, target_users="daughter",
    )
    db.add(imageless)
    db.commit()

    # 4-year-old with any theme: image-backed picture questions only
    sample_user.theme = "pony"
    db.commit()
    session = create_session(db, sample_user)
    for q in session.questions:
        char = db.query(Character).filter_by(id=q.character_id).one()
        assert char.image_url is not None
        assert q.question_mode == "char_to_image"

    # 9-year-old reader: imageless daughter-content is reachable
    reader = User(name="Reader Kid", pin="1111", age=9, theme="racing", role="child")
    db.add(reader)
    db.commit()
    from app.services.question_generator import select_characters
    pool = select_characters(db, reader.id, count=50, is_prereader=False)
    assert any(c.character == "想" for c in pool)


def test_car_level_survives_spending(db, sample_user, sample_characters):
    from app.services.session_engine import _update_car_level
    settings = get_settings()

    sample_user.coins = 5
    sample_user.lifetime_coins = 5
    assert _update_car_level(sample_user, settings) is True
    assert sample_user.car_level == 1

    # Spend everything at the store — the tier must not stall
    sample_user.coins = 0
    sample_user.lifetime_coins = 15
    assert _update_car_level(sample_user, settings) is True
    assert sample_user.car_level == 2


def test_ledger_records_coin_spending(db, sample_user, sample_characters):
    from app.models.rewards import PointsLedger
    from app.services.rewards import award_points, buy_streak_freeze
    settings = get_settings()

    # Earn enough points to convert stars into at least one coin
    award_points(db, sample_user, settings.coins_per_stars, "test_award")
    db.commit()
    conversion = db.query(PointsLedger).filter_by(user_id=sample_user.id, reason="test_award").one()
    assert conversion.coins_change == 1
    assert sample_user.lifetime_coins == 1

    assert buy_streak_freeze(db, sample_user) is True
    db.commit()
    spend = db.query(PointsLedger).filter_by(user_id=sample_user.id, reason="buy_streak_freeze").one()
    assert spend.coins_change == -1
    assert sample_user.lifetime_coins == 1  # spending never reduces lifetime earnings


def test_summary_points_include_lucky_star_bonus(db, sample_user, sample_characters, monkeypatch):
    settings = get_settings()
    session = create_session(db, sample_user)

    # Force lucky star on every answer (patched after session creation so
    # question generation randomness is untouched)
    monkeypatch.setattr("app.services.session_engine.random.random", lambda: 0.0)

    for q in session.questions:
        result = submit_answer(db, sample_user, q.id, q.correct_answer)
        assert result["bonus"] == "lucky_star"
        assert result["points_earned"] == settings.points_correct * settings.lucky_star_multiplier

    summary = complete_session(db, sample_user, session.id)

    base = len(session.questions) * settings.points_correct * settings.lucky_star_multiplier
    perfect_bonus = base * (settings.perfect_bonus_multiplier - 1)
    streak_bonus = sample_user.streak * settings.streak_bonus_multiplier
    expected = base + perfect_bonus + settings.daily_bonus + streak_bonus
    assert summary["points_earned"] == expected
    # Breakdown must account for every point in the summary
    assert sum(x["value"] for x in summary["xp_breakdown"]) == summary["points_earned"]
