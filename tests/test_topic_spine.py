"""Tests for the math/English topic spine built on the Marble Skill Taxonomy."""
import json
from datetime import date, timedelta

import pytest

from app.models.session import SessionQuestion
from app.models.topic import LearningTopic, TopicPrerequisite, UserTopicProgress
from app.models.user import User
from app.services import english_generator, math_generator
from app.services.session_engine import create_session, submit_answer
from app.services.spaced_repetition import update_topic_mastery
from app.services.topic_selection import (
    candidate_topics,
    conversation_prompts,
    select_topics,
    topic_snapshot,
)


@pytest.fixture
def kid9(db):
    user = User(name="Ellie", pin="1111", age=9, theme="pony", role="child")
    db.add(user)
    db.commit()
    return user


# ── Vendored data integrity ──

def test_vendored_taxonomy_imports(db, taxonomy):
    assert taxonomy["topics_added"] == 1325
    assert taxonomy["playable"] == 72
    assert taxonomy["edges"] > 1000
    assert db.query(LearningTopic).count() == 1325
    assert db.query(TopicPrerequisite).count() == taxonomy["edges"]


def test_every_playable_topic_maps_to_a_real_generator_mode(db, taxonomy):
    """A topic claiming to be playable must have a mode we can actually run."""
    known = math_generator.available_modes() | english_generator.available_modes()
    playable = (
        db.query(LearningTopic)
        .filter(LearningTopic.question_mode.isnot(None))
        .all()
    )
    assert playable
    for topic in playable:
        assert topic.question_mode in known, (
            f"{topic.topic_key} ({topic.name}) maps to unknown mode {topic.question_mode}"
        )
        # Math topics must use math modes and English topics English modes.
        expected = (
            math_generator.available_modes()
            if topic.subject == "Mathematics"
            else english_generator.available_modes()
        )
        assert topic.question_mode in expected


def test_reimport_is_idempotent(db, taxonomy):
    from app.seed.seed_taxonomy import import_taxonomy

    second = import_taxonomy(db)
    assert second["topics_added"] == 0
    assert second["topics_updated"] == 0
    assert db.query(LearningTopic).count() == 1325


def test_reimport_preserves_child_progress(db, taxonomy, kid9):
    from app.seed.seed_taxonomy import import_taxonomy

    topic = (
        db.query(LearningTopic)
        .filter(LearningTopic.question_mode.isnot(None))
        .first()
    )
    update_topic_mastery(db, kid9.id, topic.id, True)
    db.commit()

    import_taxonomy(db)

    rows = db.query(UserTopicProgress).filter_by(user_id=kid9.id).all()
    assert len(rows) == 1
    assert rows[0].topic_id == topic.id


# ── Selection ──

def test_candidates_are_age_appropriate(db, taxonomy, kid9):
    for topic in candidate_topics(db, 9, "Mathematics"):
        assert topic.question_mode is not None
        # Widening is allowed, but never beyond the +/-4 guard rail.
        assert topic.age_start <= 13 and topic.age_end >= 5


def test_select_topics_fills_the_session(db, taxonomy, kid9):
    topics = select_topics(db, kid9, "math", 5)
    assert len(topics) == 5
    assert all(t.subject == "Mathematics" for t in topics)


def test_select_topics_works_for_a_four_year_old(db, taxonomy, sample_user):
    """Age 4 has a thin topic pool — the session still gets 5 questions."""
    assert sample_user.age == 4
    topics = select_topics(db, sample_user, "math", 5)
    assert len(topics) == 5


def test_select_topics_returns_nothing_without_taxonomy(db, kid9):
    assert select_topics(db, kid9, "math", 5) == []


def test_unknown_game_type_selects_nothing(db, taxonomy, kid9):
    assert select_topics(db, kid9, "logic", 5) == []


def test_overdue_topics_are_prioritised(db, taxonomy, kid9):
    """A topic whose review date has passed outranks untouched topics."""
    pool = candidate_topics(db, 9, "Mathematics")
    overdue = pool[:5]
    for topic in overdue:
        progress = update_topic_mastery(db, kid9.id, topic.id, True)
        progress.next_review_date = date.today() - timedelta(days=3)
    db.commit()

    selected = {t.id for t in select_topics(db, kid9, "math", 5)}
    assert selected == {t.id for t in overdue}


def _make_topic(key, mode="multiplication_medium", **kw):
    return LearningTopic(
        topic_key=key, subject="Mathematics", domain="Test", name=key,
        age_start=8, age_end=10, question_mode=mode, **kw,
    )


def test_hard_prerequisites_gate_new_topics(db, kid9):
    """A locked topic stays out while there is enough unlocked work to do."""
    roots = [_make_topic(f"mt_root{i}") for i in range(5)]
    locked = _make_topic("mt_locked", mode="division_basic", centrality=0.9)
    db.add_all(roots + [locked])
    db.add(TopicPrerequisite(
        topic_key="mt_locked", prerequisite_key="mt_root0", strength="hard",
    ))
    db.commit()

    assert "mt_locked" not in {t.topic_key for t in select_topics(db, kid9, "math", 5)}

    # Two correct answers clears the prerequisite bar.
    update_topic_mastery(db, kid9.id, roots[0].id, True)
    update_topic_mastery(db, kid9.id, roots[0].id, True)
    db.commit()

    seen = set()
    for _ in range(20):
        seen |= {t.topic_key for t in select_topics(db, kid9, "math", 5)}
    assert "mt_locked" in seen


def test_thin_pool_admits_gated_topics_rather_than_repeating(db, kid9):
    """One root and five slots: bend the gate instead of asking it five times."""
    root = _make_topic("mt_root")
    near = _make_topic("mt_near", mode="division_basic")        # 1 unmet prereq
    far = _make_topic("mt_far", mode="addition_medium")         # 2 unmet prereqs
    db.add_all([root, near, far])
    db.add_all([
        TopicPrerequisite(topic_key="mt_near", prerequisite_key="mt_root", strength="hard"),
        TopicPrerequisite(topic_key="mt_far", prerequisite_key="mt_root", strength="hard"),
        TopicPrerequisite(topic_key="mt_far", prerequisite_key="mt_near", strength="hard"),
    ])
    db.commit()

    selected = [t.topic_key for t in select_topics(db, kid9, "math", 5)]
    assert len(selected) == 5
    # The least-blocked topic is admitted before the more distant one.
    assert "mt_near" in selected
    assert selected.count("mt_root") < 5


def test_four_year_old_math_is_not_five_identical_topics(db, taxonomy, sample_user):
    """Age-4 math is a near-linear chain — the regression this guards against."""
    assert sample_user.age == 4
    topics = select_topics(db, sample_user, "math", 5)
    assert len({t.topic_key for t in topics}) > 1


def test_soft_prerequisites_do_not_gate(db, kid9):
    base = LearningTopic(
        topic_key="mt_base", subject="Mathematics", domain="Test", name="Base",
        age_start=8, age_end=10, question_mode="multiplication_medium",
    )
    nudged = LearningTopic(
        topic_key="mt_soft", subject="Mathematics", domain="Test", name="Soft",
        age_start=8, age_end=10, question_mode="division_basic",
    )
    db.add_all([base, nudged])
    db.add(TopicPrerequisite(
        topic_key="mt_soft", prerequisite_key="mt_base", strength="soft",
    ))
    db.commit()

    assert "mt_soft" in {t.topic_key for t in select_topics(db, kid9, "math", 5)}


def test_prereq_walk_passes_through_unplayable_topics(db, kid9):
    """An unassessable prerequisite doesn't block — but its own prereq does."""
    root = LearningTopic(
        topic_key="mt_root", subject="Mathematics", domain="Test", name="Root",
        age_start=8, age_end=10, question_mode="multiplication_medium",
    )
    bridge = LearningTopic(  # no generator covers this one
        topic_key="mt_bridge", subject="Mathematics", domain="Test", name="Bridge",
        age_start=8, age_end=10, question_mode=None,
    )
    leaf = LearningTopic(
        topic_key="mt_leaf", subject="Mathematics", domain="Test", name="Leaf",
        age_start=8, age_end=10, question_mode="division_basic",
    )
    # Filler roots so the session can fill up without bending the gate.
    filler = [_make_topic(f"mt_filler{i}") for i in range(5)]
    db.add_all([root, bridge, leaf] + filler)
    db.add_all([
        TopicPrerequisite(topic_key="mt_leaf", prerequisite_key="mt_bridge", strength="hard"),
        TopicPrerequisite(topic_key="mt_bridge", prerequisite_key="mt_root", strength="hard"),
    ])
    db.commit()

    assert "mt_leaf" not in {t.topic_key for t in select_topics(db, kid9, "math", 5)}

    update_topic_mastery(db, kid9.id, root.id, True)
    update_topic_mastery(db, kid9.id, root.id, True)
    db.commit()

    seen = set()
    for _ in range(20):
        seen |= {t.topic_key for t in select_topics(db, kid9, "math", 5)}
    assert "mt_leaf" in seen


# ── Session integration ──

@pytest.mark.parametrize("game_type", ["math", "english"])
def test_sessions_are_topic_driven(db, taxonomy, kid9, game_type):
    session = create_session(db, kid9, game_type=game_type)
    questions = db.query(SessionQuestion).filter_by(session_id=session.id).all()

    assert len(questions) == 5
    for q in questions:
        assert q.topic_id is not None
        topic = db.get(LearningTopic, q.topic_id)
        assert q.question_mode == topic.question_mode
        assert len(json.loads(q.options)) == 3
        assert q.correct_answer in json.loads(q.options)


@pytest.mark.parametrize("game_type", ["math", "english"])
def test_sessions_fall_back_when_taxonomy_is_absent(db, kid9, game_type):
    """An un-migrated or un-seeded database keeps the old random rotation."""
    session = create_session(db, kid9, game_type=game_type)
    questions = db.query(SessionQuestion).filter_by(session_id=session.id).all()

    assert len(questions) == 5
    assert all(q.topic_id is None for q in questions)
    assert all(q.correct_answer in json.loads(q.options) for q in questions)


def test_answering_updates_topic_mastery(db, taxonomy, kid9):
    session = create_session(db, kid9, game_type="math")
    question = session.questions[0]

    submit_answer(db, kid9, question.id, question.correct_answer)

    progress = (
        db.query(UserTopicProgress)
        .filter_by(user_id=kid9.id, topic_id=question.topic_id)
        .first()
    )
    assert progress is not None
    assert progress.sm2_repetitions == 1
    assert progress.correct_count == 1
    assert progress.next_review_date == date.today() + timedelta(days=1)


def test_wrong_answer_schedules_immediate_topic_review(db, taxonomy, kid9):
    session = create_session(db, kid9, game_type="math")
    question = session.questions[0]
    wrong = next(o for o in json.loads(question.options) if o != question.correct_answer)

    submit_answer(db, kid9, question.id, wrong)

    progress = (
        db.query(UserTopicProgress)
        .filter_by(user_id=kid9.id, topic_id=question.topic_id)
        .first()
    )
    assert progress.sm2_repetitions == 0
    assert progress.wrong_count == 1
    assert progress.next_review_date == date.today()


def test_chinese_sessions_are_untouched(db, taxonomy, sample_user, sample_characters):
    session = create_session(db, sample_user, game_type="chinese")
    questions = db.query(SessionQuestion).filter_by(session_id=session.id).all()
    assert len(questions) == 5
    assert all(q.topic_id is None for q in questions)
    assert all(q.character_id is not None for q in questions)


# ── Dashboard helpers ──

def test_conversation_prompts_substitute_the_child_name(db, taxonomy, kid9):
    prompts = conversation_prompts(db, kid9, limit=3)
    assert len(prompts) == 3
    for p in prompts:
        assert p["prompt"]
        assert "{{name}}" not in p["prompt"]
        assert "Ellie" in p["prompt"] or "{{" not in p["prompt"]


def test_conversation_prompts_prefer_current_work(db, taxonomy, kid9):
    session = create_session(db, kid9, game_type="math")
    submit_answer(db, kid9, session.questions[0].id, session.questions[0].correct_answer)

    prompts = conversation_prompts(db, kid9, limit=3)
    assert any(p["practised"] for p in prompts)


def test_conversation_prompts_survive_an_empty_taxonomy(db, kid9):
    assert conversation_prompts(db, kid9, limit=3) == []


def test_topic_snapshot_reports_both_subjects(db, taxonomy, kid9):
    snapshot = topic_snapshot(db, kid9)
    assert {s["subject"] for s in snapshot} == {"Mathematics", "English"}
    for entry in snapshot:
        assert entry["total"] > 0
        assert entry["untouched"] == entry["total"]
        assert entry["pct"] == 0


def test_topic_snapshot_counts_mastery(db, taxonomy, kid9):
    topic = candidate_topics(db, 9, "Mathematics")[0]
    for _ in range(3):
        update_topic_mastery(db, kid9.id, topic.id, True)
    db.commit()

    maths = next(s for s in topic_snapshot(db, kid9) if s["subject"] == "Mathematics")
    assert maths["mastered"] == 1
    assert maths["untouched"] == maths["total"] - 1


def test_conversation_prompts_leave_room_beyond_practised_work(db, taxonomy, kid9):
    """At least one prompt comes from outside math/English — that's the point."""
    session = create_session(db, kid9, game_type="math")
    for q in session.questions:
        submit_answer(db, kid9, q.id, q.correct_answer)

    prompts = conversation_prompts(db, kid9, limit=3)
    assert len(prompts) == 3
    assert sum(1 for p in prompts if p["practised"]) <= 2
