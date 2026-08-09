"""Pick *what* a child practises next in math/English.

Before this, math and English sessions rolled a weighted die over a handful of
hardcoded mode strings — a 9-year-old who had nailed times tables kept getting
times tables, and nothing recorded that she had. This module gives those
subjects the same treatment Chinese characters already had: a unit of learning
(a taxonomy topic), spaced repetition over it, and a prerequisite graph so
topics arrive in an order that makes sense.

The graph and the topics come from the Marble Skill Taxonomy — see NOTICE.
"""
import json
import random
from datetime import date

from sqlalchemy.orm import Session

from app.models.topic import LearningTopic, TopicPrerequisite, UserTopicProgress
from app.models.user import User

# game_type (ours) -> subject (the taxonomy's)
SUBJECT_BY_GAME_TYPE = {
    "math": "Mathematics",
    "english": "English",
}

# SM-2 repetitions at which we treat a prerequisite as satisfied. Two correct
# answers on separate days is a low bar on purpose: a prerequisite gate that is
# too strict just starves the session and the child sees the same five topics.
PREREQ_MASTERED_REPETITIONS = 2

# How far up the prerequisite chain to walk looking for a *playable* ancestor.
# Most chains resolve in one or two hops; the cap only guards against the graph
# growing pathological later.
_PREREQ_WALK_DEPTH = 4

# Slots per session reserved for topics the child has never seen, so a big
# review backlog can't freeze progress entirely.
_NEW_TOPIC_SLOTS = 2


def _age_window(age: int, widen: int) -> tuple[int, int]:
    return age - widen, age + widen


def candidate_topics(db: Session, age: int, subject: str) -> list[LearningTopic]:
    """Playable topics whose age band contains the child, widening if too few."""
    base = (
        db.query(LearningTopic)
        .filter(LearningTopic.subject == subject)
        .filter(LearningTopic.question_mode.isnot(None))
    )
    for widen in (0, 1, 2, 4):
        low, high = _age_window(age, widen)
        found = (
            base.filter(LearningTopic.age_start <= high)
            .filter(LearningTopic.age_end >= low)
            .all()
        )
        if len(found) >= 5:
            return found
    return found


def _playable_prerequisites(
    db: Session, topic_keys: set[str], playable_keys: set[str]
) -> dict[str, set[str]]:
    """Map each topic key to the playable topics it genuinely depends on.

    Hard edges only. Where a prerequisite is a topic we can't assess (no
    generator covers it), we walk *through* it to its own prerequisites rather
    than dropping the constraint or blocking on something unmeasurable.
    """
    edges: dict[str, list[str]] = {}
    for row in db.query(TopicPrerequisite).filter(TopicPrerequisite.strength == "hard").all():
        edges.setdefault(row.topic_key, []).append(row.prerequisite_key)

    resolved: dict[str, set[str]] = {}
    for key in topic_keys:
        found: set[str] = set()
        frontier = list(edges.get(key, ()))
        seen = {key}
        for _ in range(_PREREQ_WALK_DEPTH):
            if not frontier:
                break
            next_frontier: list[str] = []
            for prereq in frontier:
                if prereq in seen:
                    continue
                seen.add(prereq)
                if prereq in playable_keys:
                    found.add(prereq)
                else:
                    next_frontier.extend(edges.get(prereq, ()))
            frontier = next_frontier
        resolved[key] = found
    return resolved


def select_topics(
    db: Session, user: User, game_type: str, count: int
) -> list[LearningTopic]:
    """Choose `count` topics for one session. Empty list = fall back to random.

    Priority: overdue reviews, then a couple of newly unlocked topics, then the
    weakest work in progress. Topics repeat only when the pool is smaller than
    the session (which is normal for a 4-year-old — there aren't many age-4
    math topics).
    """
    subject = SUBJECT_BY_GAME_TYPE.get(game_type)
    if subject is None:
        return []

    age = user.age or 5
    candidates = candidate_topics(db, age, subject)
    if not candidates:
        return []

    by_id = {t.id: t for t in candidates}
    playable_keys = {t.topic_key for t in candidates}
    prereqs = _playable_prerequisites(db, playable_keys, playable_keys)

    progress_rows = (
        db.query(UserTopicProgress)
        .filter(UserTopicProgress.user_id == user.id)
        .filter(UserTopicProgress.topic_id.in_(by_id.keys()))
        .all()
    )
    progress = {p.topic_id: p for p in progress_rows}
    mastered_keys = {
        by_id[p.topic_id].topic_key
        for p in progress_rows
        if p.sm2_repetitions >= PREREQ_MASTERED_REPETITIONS
    }

    today = date.today()
    due, in_progress, unlocked_new = [], [], []
    for topic in candidates:
        p = progress.get(topic.id)
        if p is None:
            if prereqs.get(topic.topic_key, set()) <= mastered_keys:
                unlocked_new.append(topic)
        elif p.next_review_date is not None and p.next_review_date <= today:
            due.append((p.next_review_date, p.mastery_score, topic))
        else:
            in_progress.append((p.mastery_score, topic))

    random.shuffle(unlocked_new)
    due.sort(key=lambda row: (row[0], row[1]))
    in_progress.sort(key=lambda row: row[0])

    # Foundational and high-leverage topics first among the untouched ones.
    unlocked_new.sort(key=lambda t: (t.age_start, -(t.centrality or 0.0)))

    due_q = [row[2] for row in due]
    prog_q = [row[1] for row in in_progress]

    selected: list[LearningTopic] = []
    selected.extend(due_q[:count])

    if len(selected) < count:
        room = count - len(selected)
        take_new = min(_NEW_TOPIC_SLOTS, room, len(unlocked_new))
        selected.extend(unlocked_new[:take_new])

    if len(selected) < count:
        selected.extend(prog_q[: count - len(selected)])

    if len(selected) < count:
        already = {t.id for t in selected}
        selected.extend(t for t in unlocked_new if t.id not in already)
        selected = selected[:count]

    if len(selected) < count:
        # Everything unlocked is already in the session and it still isn't full.
        # Age-4 math is a near-linear chain, so a cold-start 4-year-old has
        # exactly one root topic — five identical "How many?" prompts. Admit the
        # least-blocked topics next instead: genuinely-ready work still comes
        # first, and the gate only bends when it would otherwise starve.
        already = {t.id for t in selected}
        gated = sorted(
            (
                t for t in candidates
                if t.id not in already and t.id not in progress
                and prereqs.get(t.topic_key)
            ),
            key=lambda t: (
                len(prereqs[t.topic_key] - mastered_keys),
                t.age_start,
                -(t.centrality or 0.0),
            ),
        )
        selected.extend(gated[: count - len(selected)])

    if not selected:
        return []

    # Still short (the whole subject has fewer topics than a session holds):
    # cycle rather than short-change the child.
    pool = list(selected)
    i = 0
    while len(selected) < count:
        selected.append(pool[i % len(pool)])
        i += 1

    random.shuffle(selected)
    return selected[:count]


# ── Dashboard helpers ──

def _fill_name(prompt: str | None, child_name: str) -> str | None:
    """Substitute the taxonomy's {{name}} placeholder with the child's name."""
    if not prompt:
        return None
    return prompt.replace("{{name}}", child_name)


def conversation_prompts(
    db: Session, child: User, limit: int = 3
) -> list[dict]:
    """Offline check-in questions for a parent to ask away from the iPad.

    Drawn first from what the child is actually working on, then from
    age-appropriate topics across every subject — including the ones no
    generator can quiz (science, history, life skills), which is most of them.
    """
    age = child.age or 5
    name = child.name

    # Leave at least one slot for something outside the app. Math and English
    # are the only subjects the child can practise here, so filling every slot
    # from recent work would hide the ~1,250 science/history/life-skills topics
    # that are the whole point of asking away from the iPad.
    working_slots = max(1, limit - 1)
    working_on = (
        db.query(LearningTopic)
        .join(UserTopicProgress, UserTopicProgress.topic_id == LearningTopic.id)
        .filter(UserTopicProgress.user_id == child.id)
        .filter(LearningTopic.assessment_prompt.isnot(None))
        .order_by(UserTopicProgress.last_seen.desc())
        .limit(working_slots)
        .all()
    )

    picked = list(working_on)
    picked_ids = {t.id for t in picked}

    if len(picked) < limit:
        pool = (
            db.query(LearningTopic)
            .filter(LearningTopic.age_start <= age)
            .filter(LearningTopic.age_end >= age)
            .filter(LearningTopic.assessment_prompt.isnot(None))
            .order_by(LearningTopic.centrality.desc())
            .limit(60)
            .all()
        )
        extras = [t for t in pool if t.id not in picked_ids]
        random.shuffle(extras)
        picked.extend(extras[: limit - len(picked)])

    return [
        {
            "subject": t.subject,
            "domain": t.domain,
            "name": t.name,
            "prompt": _fill_name(t.assessment_prompt, name),
            "evidence": json.loads(t.evidence) if t.evidence else [],
            "practised": t.id in {w.id for w in working_on},
        }
        for t in picked
    ]


def topic_snapshot(db: Session, child: User) -> list[dict]:
    """Per-subject topic progress for the dashboard: mastered / started / next."""
    out = []
    for game_type, subject in SUBJECT_BY_GAME_TYPE.items():
        candidates = candidate_topics(db, child.age or 5, subject)
        if not candidates:
            continue
        by_id = {t.id: t for t in candidates}

        rows = (
            db.query(UserTopicProgress)
            .filter(UserTopicProgress.user_id == child.id)
            .filter(UserTopicProgress.topic_id.in_(by_id.keys()))
            .all()
        )
        mastered = [r for r in rows if r.sm2_repetitions >= 3]
        started = [r for r in rows if 0 < r.sm2_repetitions < 3]

        weakest = sorted(
            rows, key=lambda r: (r.mastery_score, -(r.wrong_count or 0))
        )[:3]

        out.append({
            "game_type": game_type,
            "subject": subject,
            "total": len(candidates),
            "mastered": len(mastered),
            "started": len(started),
            "untouched": len(candidates) - len(rows),
            "pct": round(len(mastered) / len(candidates) * 100) if candidates else 0,
            "weakest": [
                {
                    "name": by_id[r.topic_id].name,
                    "domain": by_id[r.topic_id].domain,
                    "mastery": r.mastery_score,
                    "wrong": r.wrong_count or 0,
                }
                for r in weakest
            ],
        })
    return out


def drill_topics(db: Session, topic_ids: list[int] | None, count: int) -> list[LearningTopic]:
    """Expand a parent-queued drill into a full session's worth of topics.

    A drill is a deliberate override: the parent picked these, so spaced
    repetition doesn't get a say. Fewer topics than questions means the topics
    cycle — five questions on two shaky topics is exactly the point of a drill.
    """
    if not topic_ids:
        return []

    found = (
        db.query(LearningTopic)
        .filter(LearningTopic.id.in_(topic_ids))
        .filter(LearningTopic.question_mode.isnot(None))
        .all()
    )
    if not found:
        return []

    # Preserve the order the dashboard queued them in (weakest first).
    order = {tid: i for i, tid in enumerate(topic_ids)}
    found.sort(key=lambda t: order.get(t.id, len(order)))

    selected = []
    while len(selected) < count:
        selected.append(found[len(selected) % len(found)])
    return selected[:count]


def weakest_topics(db: Session, child: User, game_type: str, limit: int = 5) -> list[LearningTopic]:
    """Topics worth drilling for this child: overdue first, then weakest.

    Only topics they have actually attempted — drilling something never seen
    would be teaching, not drilling, and the session engine already introduces
    new topics on its own.
    """
    subject = SUBJECT_BY_GAME_TYPE.get(game_type)
    if subject is None:
        return []

    today = date.today()
    rows = (
        db.query(UserTopicProgress, LearningTopic)
        .join(LearningTopic, UserTopicProgress.topic_id == LearningTopic.id)
        .filter(UserTopicProgress.user_id == child.id)
        .filter(LearningTopic.subject == subject)
        .filter(LearningTopic.question_mode.isnot(None))
        .all()
    )
    if not rows:
        return []

    def rank(pair):
        progress, _ = pair
        overdue = (
            progress.next_review_date is not None and progress.next_review_date <= today
        )
        return (
            0 if overdue else 1,
            progress.mastery_score or 0,
            -(progress.wrong_count or 0),
        )

    rows.sort(key=rank)
    return [topic for _, topic in rows[:limit]]
