"""Seed collectibles data for garage."""

from sqlalchemy.orm import Session
from app.models import CollectibleItem
from app.database import SessionLocal


COLLECTIBLES = [
    # Cars
    {"item_type": "car", "item_key": "starter_car", "name": "Starter Racer", "emoji": "🚗", "rarity": "common", "price_coins": 0},
    {"item_type": "car", "item_key": "blue_speedster", "name": "Blue Speedster", "emoji": "🏎️", "rarity": "common", "price_coins": 10},
    {"item_type": "car", "item_key": "red_rocket", "name": "Red Rocket", "emoji": "🚘", "rarity": "rare", "price_coins": 25},
    {"item_type": "car", "item_key": "police_cruiser", "name": "Police Cruiser", "emoji": "🚓", "rarity": "rare", "price_coins": 30},
    {"item_type": "car", "item_key": "taxi", "name": "Yellow Taxi", "emoji": "🚕", "rarity": "common", "price_coins": 15},
    {"item_type": "car", "item_key": "formula_one", "name": "Formula One", "emoji": "🏁", "rarity": "epic", "price_coins": 50},
    {"item_type": "car", "item_key": "golden_car", "name": "Golden Champion", "emoji": "⭐", "rarity": "legendary", "price_coins": 100, 
     "unlock_requirement": "Reach 30-day streak"},
    
    # Pets
    {"item_type": "pet", "item_key": "no_pet", "name": "No Pet", "emoji": "✖️", "rarity": "common", "price_coins": 0},
    {"item_type": "pet", "item_key": "dog", "name": "Puppy Pal", "emoji": "🐶", "rarity": "common", "price_coins": 5},
    {"item_type": "pet", "item_key": "cat", "name": "Kitty Friend", "emoji": "🐱", "rarity": "common", "price_coins": 5},
    {"item_type": "pet", "item_key": "rabbit", "name": "Bouncy Bunny", "emoji": "🐰", "rarity": "rare", "price_coins": 15},
    {"item_type": "pet", "item_key": "panda", "name": "Panda Buddy", "emoji": "🐼", "rarity": "rare", "price_coins": 20},
    {"item_type": "pet", "item_key": "unicorn", "name": "Magic Unicorn", "emoji": "🦄", "rarity": "epic", "price_coins": 40},
    {"item_type": "pet", "item_key": "dragon", "name": "Fire Dragon", "emoji": "🐉", "rarity": "legendary", "price_coins": 80,
     "unlock_requirement": "Complete 100 sessions"},
    
    # Themes
    {"item_type": "theme", "item_key": "default", "name": "Classic Theme", "emoji": "🎨", "rarity": "common", "price_coins": 0},
    {"item_type": "theme", "item_key": "night", "name": "Night Mode", "emoji": "🌙", "rarity": "common", "price_coins": 8},
    {"item_type": "theme", "item_key": "ocean", "name": "Ocean Theme", "emoji": "🌊", "rarity": "rare", "price_coins": 18},
    {"item_type": "theme", "item_key": "forest", "name": "Forest Theme", "emoji": "🌲", "rarity": "rare", "price_coins": 18},
    {"item_type": "theme", "item_key": "space", "name": "Space Theme", "emoji": "🚀", "rarity": "epic", "price_coins": 35},
    {"item_type": "theme", "item_key": "rainbow", "name": "Rainbow Theme", "emoji": "🌈", "rarity": "legendary", "price_coins": 75,
     "unlock_requirement": "Achieve 95% overall accuracy"},
    
    # Trails
    {"item_type": "trail", "item_key": "no_trail", "name": "No Trail", "emoji": "✖️", "rarity": "common", "price_coins": 0},
    {"item_type": "trail", "item_key": "sparkles", "name": "Sparkle Trail", "emoji": "✨", "rarity": "common", "price_coins": 3},
    {"item_type": "trail", "item_key": "stars", "name": "Star Trail", "emoji": "⭐", "rarity": "common", "price_coins": 3},
    {"item_type": "trail", "item_key": "fire", "name": "Fire Trail", "emoji": "🔥", "rarity": "rare", "price_coins": 12},
    {"item_type": "trail", "item_key": "rainbow", "name": "Rainbow Trail", "emoji": "🌈", "rarity": "epic", "price_coins": 28},
    {"item_type": "trail", "item_key": "lightning", "name": "Lightning Trail", "emoji": "⚡", "rarity": "legendary", "price_coins": 60,
     "unlock_requirement": "Complete 10 perfect sessions"},
]


def seed_collectibles(db: Session):
    """Seed collectible items."""
    for item_data in COLLECTIBLES:
        existing = db.query(CollectibleItem).filter(
            CollectibleItem.item_key == item_data["item_key"]
        ).first()
        
        if not existing:
            item = CollectibleItem(**item_data)
            db.add(item)
    
    db.commit()
    print(f"Seeded {len(COLLECTIBLES)} collectible items")


def main():
    db = SessionLocal()
    try:
        seed_collectibles(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
