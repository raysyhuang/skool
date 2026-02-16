import json
from datetime import date

from app.models.user import User
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
