import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.store import StoreItem, UserInventory

router = APIRouter(prefix="/game/store")
templates = Jinja2Templates(directory="templates")


# Seed store items (created on first access if missing)
STORE_SEED = [
    # Car skins
    {"key": "car_fire_truck", "name": "Fire Truck", "category": "car_skin", "price_coins": 2, "emoji": "\U0001F692"},
    {"key": "car_ambulance", "name": "Ambulance", "category": "car_skin", "price_coins": 2, "emoji": "\U0001F691"},
    {"key": "car_tractor", "name": "Tractor", "category": "car_skin", "price_coins": 3, "emoji": "\U0001F69C"},
    {"key": "car_motorcycle", "name": "Motorcycle", "category": "car_skin", "price_coins": 3, "emoji": "\U0001F3CD\uFE0F"},
    {"key": "car_pickup", "name": "Pickup Truck", "category": "car_skin", "price_coins": 4, "emoji": "\U0001F6FB"},
    # Backgrounds
    {"key": "bg_sunset", "name": "Sunset Road", "category": "background", "price_coins": 2, "emoji": "\U0001F305"},
    {"key": "bg_rainbow", "name": "Rainbow Road", "category": "background", "price_coins": 3, "emoji": "\U0001F308"},
    {"key": "bg_moon", "name": "Moon Highway", "category": "background", "price_coins": 3, "emoji": "\U0001F319"},
    {"key": "bg_volcano", "name": "Volcano Track", "category": "background", "price_coins": 4, "emoji": "\U0001F30B"},
    {"key": "bg_underwater", "name": "Underwater", "category": "background", "price_coins": 5, "emoji": "\U0001F30A"},
    # Trail effects
    {"key": "trail_fire", "name": "Fire Trail", "category": "trail_effect", "price_coins": 2, "emoji": "\U0001F525"},
    {"key": "trail_stars", "name": "Star Trail", "category": "trail_effect", "price_coins": 2, "emoji": "\u2B50"},
    {"key": "trail_rainbow", "name": "Rainbow Trail", "category": "trail_effect", "price_coins": 3, "emoji": "\U0001F308"},
    {"key": "trail_lightning", "name": "Lightning Trail", "category": "trail_effect", "price_coins": 4, "emoji": "\u26A1"},
    {"key": "trail_sparkle", "name": "Sparkle Trail", "category": "trail_effect", "price_coins": 3, "emoji": "\u2728"},
]


def _ensure_store_seeded(db: Session):
    """Create store items if they don't exist."""
    existing = db.query(StoreItem.key).all()
    existing_keys = {r[0] for r in existing}
    for item in STORE_SEED:
        if item["key"] not in existing_keys:
            db.add(StoreItem(**item))
    db.commit()


def _get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


@router.get("/")
def store_page(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    _ensure_store_seeded(db)

    # Get all items
    items = db.query(StoreItem).order_by(StoreItem.category, StoreItem.price_coins).all()

    # Get user's inventory
    owned = db.query(UserInventory.item_key).filter_by(user_id=user.id).all()
    owned_keys = {r[0] for r in owned}

    # Group by category
    categories = {}
    for item in items:
        cat = item.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "key": item.key,
            "name": item.name,
            "emoji": item.emoji,
            "price": item.price_coins,
            "owned": item.key in owned_keys,
            "equipped": (
                (cat == "car_skin" and user.equipped_car_skin == item.key) or
                (cat == "background" and user.equipped_background == item.key) or
                (cat == "trail_effect" and user.equipped_trail == item.key)
            ),
        })

    cat_labels = {
        "car_skin": "Car Skins",
        "background": "Backgrounds",
        "trail_effect": "Trail Effects",
    }

    return templates.TemplateResponse("store.html", {
        "request": request,
        "user": user,
        "categories": categories,
        "cat_labels": cat_labels,
    })


class BuyRequest(BaseModel):
    item_key: str


@router.post("/buy")
def buy_item(request: Request, body: BuyRequest, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    item = db.query(StoreItem).filter_by(key=body.item_key).first()
    if not item:
        return JSONResponse({"error": "Item not found"}, status_code=404)

    # Check if already owned
    existing = db.query(UserInventory).filter_by(user_id=user.id, item_key=body.item_key).first()
    if existing:
        return JSONResponse({"error": "Already owned"}, status_code=400)

    if user.coins < item.price_coins:
        return JSONResponse({"error": "Not enough coins"}, status_code=400)

    user.coins -= item.price_coins
    db.add(UserInventory(user_id=user.id, item_key=body.item_key))
    db.commit()

    return JSONResponse({
        "success": True,
        "coins": user.coins,
        "item_key": body.item_key,
    })


class EquipRequest(BaseModel):
    item_key: str


@router.post("/equip")
def equip_item(request: Request, body: EquipRequest, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    # Check owned
    owned = db.query(UserInventory).filter_by(user_id=user.id, item_key=body.item_key).first()
    if not owned:
        return JSONResponse({"error": "Not owned"}, status_code=400)

    item = db.query(StoreItem).filter_by(key=body.item_key).first()
    if not item:
        return JSONResponse({"error": "Item not found"}, status_code=404)

    if item.category == "car_skin":
        user.equipped_car_skin = body.item_key
    elif item.category == "background":
        user.equipped_background = body.item_key
    elif item.category == "trail_effect":
        user.equipped_trail = body.item_key

    db.commit()

    return JSONResponse({
        "success": True,
        "equipped": body.item_key,
        "category": item.category,
    })
