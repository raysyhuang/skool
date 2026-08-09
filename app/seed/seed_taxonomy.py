"""Import the vendored Marble Skill Taxonomy subset into the database.

Idempotent: safe to re-run after `python scripts/build_taxonomy.py` refreshes
the JSON. Existing rows are updated in place so a child's UserTopicProgress
(which points at learning_topics.id) survives a re-import.

    python -m app.seed.seed_taxonomy
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine, SessionLocal, Base  # noqa: E402
from app.models import *  # noqa: F401,F403,E402  ensure all models are registered
from app.models.topic import LearningTopic, TopicPrerequisite  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taxonomy")


def _load(name: str) -> dict:
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def import_taxonomy(db) -> dict:
    """Upsert topics and prerequisite edges. Returns a counts summary."""
    topics = _load("topics.json")["topics"]
    deps = _load("dependencies.json")["dependencies"]

    existing = {t.topic_key: t for t in db.query(LearningTopic).all()}

    added = updated = 0
    for row in topics:
        fields = {
            "subject": row["subject"],
            "domain": row["domain"],
            "name": row["name"],
            "description": row.get("description"),
            "topic_type": row.get("type"),
            "age_start": row["ageRangeStart"],
            "age_end": row["ageRangeEnd"],
            "centrality": row.get("centrality") or 0.0,
            "evidence": json.dumps(row.get("evidence") or [], ensure_ascii=False),
            "assessment_prompt": row.get("assessmentPrompt"),
            "question_mode": row.get("questionMode"),
        }
        topic = existing.get(row["id"])
        if topic is None:
            db.add(LearningTopic(topic_key=row["id"], **fields))
            added += 1
        else:
            changed = False
            for key, value in fields.items():
                if getattr(topic, key) != value:
                    setattr(topic, key, value)
                    changed = True
            updated += int(changed)

    # Edges carry no per-child state, so replacing them wholesale is safe and
    # keeps deletions upstream from lingering.
    edge_count = db.query(TopicPrerequisite).delete()
    for edge in deps:
        db.add(TopicPrerequisite(
            topic_key=edge["topicId"],
            prerequisite_key=edge["prerequisiteId"],
            strength=edge.get("strength", "hard"),
            reason=edge.get("reason"),
        ))

    db.commit()
    return {
        "topics_added": added,
        "topics_updated": updated,
        "edges_replaced": edge_count,
        "edges": len(deps),
        "playable": sum(1 for t in topics if t.get("questionMode")),
    }


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = import_taxonomy(db)
        print(
            f"Taxonomy: +{result['topics_added']} topics, "
            f"{result['topics_updated']} updated, "
            f"{result['playable']} playable, "
            f"{result['edges']} prerequisite edges."
        )
    except Exception as exc:
        db.rollback()
        print(f"Error importing taxonomy: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
