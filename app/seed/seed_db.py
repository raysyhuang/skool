"""Seed the database with initial users and characters."""
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.character import Character
from app.models import *  # noqa: ensure all models are registered


def _load_chars_data():
    """Load character data from the JSON seed file."""
    seed_dir = os.path.dirname(os.path.abspath(__file__))
    chars_file = os.path.join(seed_dir, "characters_son.json")
    with open(chars_file, "r", encoding="utf-8") as f:
        return json.load(f)


def add_chars():
    """Add only new characters to an existing database, preserving all user/progress data."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        chars_data = _load_chars_data()

        # Get all existing characters by their character field
        existing = set(
            row[0] for row in db.query(Character.character).all()
        )

        new_count = 0
        for item in chars_data:
            if item["character"] not in existing:
                db.add(Character(**item))
                new_count += 1

        db.commit()
        print(f"Added {new_count} new characters ({len(existing)} already existed).")

    except Exception as e:
        db.rollback()
        print(f"Error adding characters: {e}")
        raise
    finally:
        db.close()


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already seeded. Skipping.")
            return

        # Create users
        son = User(
            name="Daniel",
            pin="0000",
            age=4,
            theme="racing",
            role="child",
        )
        daughter = User(
            name="Ellie",
            pin="1111",
            age=9,
            theme="pony",
            role="child",
        )
        parent = User(
            name="爸爸",
            pin="8888",
            age=None,
            theme="racing",
            role="parent",
        )
        db.add_all([son, daughter, parent])
        db.flush()
        print(f"Created users: {son.name} (id={son.id}), {daughter.name} (id={daughter.id}), {parent.name} (id={parent.id})")

        # Load characters
        chars_data = _load_chars_data()

        for item in chars_data:
            char = Character(**item)
            db.add(char)

        db.commit()
        print(f"Seeded {len(chars_data)} characters.")
        print("Done! Users:")
        print(f"  Daniel (son)     - PIN: 0000 - Theme: racing")
        print(f"  Ellie  (daughter) - PIN: 1111 - Theme: racing")
        print(f"  爸爸   (parent)   - PIN: 8888")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if "--add-chars" in sys.argv:
        add_chars()
    else:
        seed()
