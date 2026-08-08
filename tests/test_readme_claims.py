"""Keep the countable claims in README.md honest.

These drifted silently: the README advertised 500 words when the seed held
540, 220+ SVG icons when 219 exist, and Ellie at 8 when she is seeded at 9 —
and her age decides which learning topics she is served, so that one is not
merely cosmetic.
"""
import json
import os
import re

README = "README.md"


def _readme() -> str:
    return open(README, encoding="utf-8").read()


def test_advertised_character_count_matches_the_seed():
    stated = int(re.search(r"\*\*(\d+) Chinese words", _readme()).group(1))
    actual = len(json.load(open("app/seed/characters_son.json", encoding="utf-8")))
    assert stated == actual, f"README says {stated} characters, seed has {actual}"


def test_advertised_icon_count_matches_the_directory():
    stated = int(re.search(r"\*\*(\d+) custom SVG icons", _readme()).group(1))
    actual = len([f for f in os.listdir("static/images/chars") if f.endswith(".svg")])
    assert stated == actual, f"README says {stated} icons, {actual} exist"


def test_documented_ages_match_the_seeded_users():
    """Age drives topic selection, so a stale README here misleads about behaviour."""
    seed = open("app/seed/seed_db.py", encoding="utf-8").read()
    readme = _readme()

    for name in ("Daniel", "Ellie"):
        block = seed.split(f'name="{name}"')[1][:200]
        seeded = int(re.search(r"age=(\d+)", block).group(1))
        row = next(l for l in readme.splitlines() if l.startswith(f"| {name} "))
        documented = int(re.search(r"(\d+)yo", row).group(1))
        assert documented == seeded, (
            f"README lists {name} at {documented}, seed_db creates them at {seeded}"
        )


def test_readme_does_not_claim_children_have_a_pin():
    """Kids tap an avatar; only the parent dashboard is PIN-gated."""
    assert "**Auth:** 4-digit PIN + session cookie" not in _readme(), (
        "README overstates auth — child logins take no PIN"
    )
    login = open("app/routes/auth.py", encoding="utf-8").read()
    child_login = login.split("def login(")[1].split("def ")[0]
    assert "pin" not in child_login, (
        "child login now takes a PIN — update the README claim this test guards"
    )
