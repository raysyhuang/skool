"""Theme configuration: copy, sprites, colors, and tier ladders per theme.

A theme is a reskin of the shared racing engine (palette override CSS +
copy + emoji), not a separate set of templates. resolve_theme_template()
in routes/game.py keeps serving the racing templates, which read their
user-facing copy from these dicts.
"""

THEMES = {
    "racing": {
        "extra_css": None,
        "body_class": "racing-theme",
        "page_title": "Race!",
        "progress_noun": "Stop",
        "marker_emoji": "\U0001F3C1",           # chequered flag
        "clouds": ["☁️", "⛅", "☁️"],
        "finish_title": "Race Complete!",
        "perfect_title": "\U0001F31F Perfect Race! \U0001F31F",
        "again_label": "Race Again!",
        "rest_title": "The car is resting! \U0001F634",
        "rest_msg": "Great racing today!",
        "rest_sprite": "\U0001F697",             # car
        "confetti": ["#ff6b35", "#fdcb6e", "#00b894", "#e84393",
                     "#6c5ce7", "#74b9ff", "#fd79a8", "#ffeaa7"],
        "tiers": [
            {"emoji": "\U0001F3CE️", "name": "Go-kart"},      # 0 coins
            {"emoji": "\U0001F697", "name": "Sedan"},               # 5 coins
            {"emoji": "\U0001F3CE️", "name": "Sports Car"},   # 15 coins
            {"emoji": "\U0001F3C1", "name": "Race Car"},            # 30 coins
            {"emoji": "\U0001F680", "name": "F1 Car"},              # 50 coins
        ],
    },
    "pony": {
        "extra_css": "pony.css",
        "body_class": "racing-theme pony-theme",
        "page_title": "Gallop!",
        "progress_noun": "Meadow",
        "marker_emoji": "\U0001F308",            # rainbow
        "clouds": ["\U0001F338", "\U0001F98B", "☁️"],
        "finish_title": "You Galloped Home!",
        "perfect_title": "\U0001F31F Perfect Gallop! \U0001F31F",
        "again_label": "Gallop Again!",
        "rest_title": "The pony is resting! \U0001F634",
        "rest_msg": "Great galloping today!",
        "rest_sprite": "\U0001F434",             # horse face
        "confetti": ["#e84393", "#a29bfe", "#ffd6e8", "#ffeaa7",
                     "#fd79a8", "#fab1d9", "#81ecec", "#ffffff"],
        "tiers": [
            {"emoji": "\U0001F434", "name": "Pony"},                       # 0 coins
            {"emoji": "\U0001F40E", "name": "Show Pony"},                  # 5 coins
            {"emoji": "\U0001F984", "name": "Unicorn"},                    # 15 coins
            {"emoji": "✨\U0001F984", "name": "Star Unicorn"},         # 30 coins
            {"emoji": "\U0001F308\U0001F984", "name": "Rainbow Unicorn"},  # 50 coins
        ],
    },
}


def get_theme(user) -> dict:
    """Theme config for a user, falling back to racing for unknown themes."""
    return THEMES.get(getattr(user, "theme", None) or "racing", THEMES["racing"])
