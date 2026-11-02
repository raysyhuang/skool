"""Parent dashboard question-level detail: accuracy split, confusions, reports."""
import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import create_app
from app.models.content_report import ContentReport
from app.models.session import GameSession, SessionQuestion
from app.models.topic import LearningTopic
from app.models.user import User
from app.services.topic_selection import SUBJECT_BY_GAME_TYPE


def _client(db) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, base_url="https://testserver")  # cookies are https_only


def _parent_client(db) -> TestClient:
    db.add(User(name="Dad", pin="8888", theme="racing", role="parent"))
    db.commit()
    client = _client(db)
    client.post("/login/parent", data={"pin": "8888"}, follow_redirects=False)
    return client


def _session(db, user, game_type="chinese", days_ago=0) -> GameSession:
    started = datetime.now(timezone.utc) - timedelta(days=days_ago)
    s = GameSession(user_id=user.id, game_type=game_type, started_at=started, completed_at=started)
    db.add(s)
    db.commit()
    return s


def _q(db, session, n, *, correct, selected, is_correct, first_ok=None, hint=False,
       mode="char_to_meaning", char=None, topic_id=None, prompt_data=None) -> SessionQuestion:
    q = SessionQuestion(
        session_id=session.id, question_number=n, question_mode=mode,
        character_id=char.id if char else None, topic_id=topic_id,
        correct_answer=correct, options=json.dumps([correct, selected]),
        prompt_data=prompt_data, selected_answer=selected, is_correct=is_correct,
        first_attempt_correct=first_ok, hint_shown=hint, first_try=not hint,
        answered_at=datetime.now(timezone.utc),
    )
    db.add(q)
    db.commit()
    return q


def test_accuracy_split_hint_rate_and_confusions(db, sample_user, sample_characters):
    big, small = sample_characters[0], sample_characters[1]
    s = _session(db, sample_user)
    # Wrong first, right on retry (selected overwritten by the retry)
    _q(db, s, 1, correct="big", selected="big", is_correct=True, first_ok=False, hint=True, char=big)
    # Right first time
    _q(db, s, 2, correct="small", selected="small", is_correct=True, first_ok=True, char=small)
    # Wrong twice on picture mode: big's picture confused with small's
    for n in (3, 4):
        _q(db, s, n, correct=big.image_url, selected=small.image_url, is_correct=False,
           first_ok=False, mode="char_to_image", char=big)
    # Old row without first_attempt_correct falls back to is_correct
    _q(db, s, 5, correct="大", selected="小", is_correct=False, mode="meaning_to_char", char=big)
    # Outside the 14-day window: ignored
    old = _session(db, sample_user, days_ago=20)
    _q(db, old, 1, correct="大", selected="人", is_correct=False, first_ok=False, char=big)

    resp = _parent_client(db).get("/dashboard/")
    assert resp.status_code == 200
    html = resp.text
    assert "Question Detail" in html
    detail = " ".join(html.split("Question Detail", 1)[1].split("Often Confuses", 1)[0].split())
    assert '<div class="val">20%</div> <div class="lbl">First-Try Right</div>' in detail  # 1/5
    assert '<div class="val">40%</div> <div class="lbl">Right Eventually</div>' in detail  # 2/5
    assert '<div class="val">20%</div> <div class="lbl">Used a Hint</div>' in detail  # 1/5
    assert "Often Confuses" in html
    assert f'src="{small.image_url}"' in html          # picture options are shown as pictures
    assert "大 (big)" in html and "小 (small)" in html  # characters get their meaning
    assert f"/dashboard/drill/{sample_user.id}?char_id={big.id}" in html
    assert "2&times;" in html
    assert "人" not in html.split("Often Confuses", 1)[1].split("Review Schedule", 1)[0]


def test_question_insights_values(db, sample_user, sample_characters):
    from app.routes.dashboard import _CharLookup, question_insights

    big, small = sample_characters[0], sample_characters[1]
    s = _session(db, sample_user)
    _q(db, s, 1, correct="big", selected="big", is_correct=True, first_ok=False, hint=True, char=big)
    _q(db, s, 2, correct="big", selected="small", is_correct=False, first_ok=False, char=big)
    _q(db, s, 3, correct="small", selected="small", is_correct=True, first_ok=True, char=small)
    _q(db, s, 4, correct="big", selected="small", is_correct=False, first_ok=False, char=big)

    ins = question_insights(db, sample_user, _CharLookup(db))
    assert ins["answered"] == 4
    assert ins["first_try_pct"] == 25
    assert ins["eventual_pct"] == 50
    assert ins["hint_pct"] == 25
    top = ins["confusions"][0]
    assert top["count"] == 2
    assert top["correct"]["text"] == "big (大)"
    assert top["selected"]["text"] == "small (小)"
    assert top["char_id"] == big.id
    assert len(ins["recent_wrong"]) == 2


def test_focused_char_drill_queues_that_char_first(db, sample_user, sample_characters):
    big = sample_characters[3]
    resp = _parent_client(db).post(f"/dashboard/drill/{sample_user.id}?char_id={big.id}")
    assert resp.status_code == 200, resp.text
    db.refresh(sample_user)
    assert json.loads(sample_user.pending_drill_char_ids) == [big.id]


def test_focused_topic_drill_queues_only_that_topic(db, sample_user, taxonomy):
    topic = (
        db.query(LearningTopic)
        .filter_by(subject=SUBJECT_BY_GAME_TYPE["math"])
        .filter(LearningTopic.question_mode.isnot(None))
        .first()
    )
    client = _parent_client(db)
    resp = client.post(f"/dashboard/drill-topics/{sample_user.id}/math?topic_id={topic.id}")
    assert resp.status_code == 200, resp.text
    db.refresh(sample_user)
    assert json.loads(sample_user.pending_drill_topic_ids) == [topic.id]

    # A topic from the other subject is refused
    other = (
        db.query(LearningTopic)
        .filter(LearningTopic.subject != SUBJECT_BY_GAME_TYPE["math"])
        .filter(LearningTopic.question_mode.isnot(None))
        .first()
    )
    resp = client.post(f"/dashboard/drill-topics/{sample_user.id}/math?topic_id={other.id}")
    assert resp.status_code == 404


def test_math_confusion_offers_topic_drill(db, sample_user, taxonomy):
    topic = (
        db.query(LearningTopic)
        .filter_by(subject=SUBJECT_BY_GAME_TYPE["math"])
        .filter(LearningTopic.question_mode.isnot(None))
        .first()
    )
    s = _session(db, sample_user, game_type="math")
    _q(db, s, 1, correct="7", selected="6", is_correct=False, first_ok=False,
       mode="math_add", topic_id=topic.id, prompt_data=json.dumps({"expression": "3 + 4"}))

    html = _parent_client(db).get("/dashboard/").text
    assert "3 + 4" in html
    assert f"/dashboard/drill-topics/{sample_user.id}/math?topic_id={topic.id}" in html


def test_report_snapshot_dedupe_and_resolve(db, sample_user, sample_characters):
    big = sample_characters[0]
    s = _session(db, sample_user)
    q = _q(db, s, 1, correct="big", selected="small", is_correct=False, first_ok=False, char=big)
    client = _parent_client(db)

    html = client.get("/dashboard/").text
    assert f"reportQuestion(this, {q.id})" in html

    resp = client.post(f"/dashboard/report/{q.id}", json={"note": "  two answers fit  "})
    assert resp.status_code == 200
    report = db.query(ContentReport).one()
    assert report.user_id == sample_user.id
    assert report.session_question_id == q.id
    assert report.mode == "char_to_meaning"
    assert report.prompt == "大 (big)"
    assert report.correct_answer == "big"
    assert report.selected_answer == "small"
    assert report.note == "two answers fit"
    assert report.resolved is False

    # Reporting again doesn't duplicate; body is optional
    assert client.post(f"/dashboard/report/{q.id}").json()["id"] == report.id
    assert db.query(ContentReport).count() == 1

    html = client.get("/dashboard/").text
    assert "Reported Questions (1)" in html
    assert f"reportQuestion(this, {q.id})" not in html

    resp = client.post(f"/dashboard/report/{report.id}/resolve")
    assert resp.json() == {"id": report.id, "resolved": True}
    assert "Reported Questions" not in client.get("/dashboard/").text
    assert client.post(f"/dashboard/report/{report.id}/resolve").json()["resolved"] is False


def test_report_endpoints_are_parent_only(db, sample_user, sample_characters):
    s = _session(db, sample_user)
    q = _q(db, s, 1, correct="big", selected="small", is_correct=False, char=sample_characters[0])

    anon = _client(db)
    assert anon.post(f"/dashboard/report/{q.id}").status_code == 403

    kid = _client(db)
    kid.post("/login", data={"user_id": sample_user.id}, follow_redirects=False)
    assert kid.post(f"/dashboard/report/{q.id}").status_code == 403
    assert kid.post("/dashboard/report/1/resolve").status_code == 403
    assert db.query(ContentReport).count() == 0


def test_report_unknown_question_404(db):
    assert _parent_client(db).post("/dashboard/report/999").status_code == 404
