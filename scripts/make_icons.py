"""Generate the PWA app icons in static/icons/.

The manifest, the service worker precache list, and base.html's apple-touch-icon
all pointed at icon-192.png / icon-512.png, but static/icons/ never existed — so
"Add to Home Screen" on the iPad had no icon to use. This draws them.

Run only when the icon design changes; the PNGs are committed. Pillow is a
build-time dependency, deliberately not in requirements.txt.

    pip install Pillow && python scripts/make_icons.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

# Matches manifest.json theme_color / background_color.
TOP = (102, 126, 234)      # #667eea
BOTTOM = (118, 75, 162)    # #764ba2
GLYPH = "学"               # "learn" — the app is Chinese-first

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]

OUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "static", "icons"
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(
        "No CJK font found. Install one of: " + ", ".join(FONT_CANDIDATES)
    )


def build(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Vertical gradient on a rounded square. iOS masks the corners itself, but
    # Android and the browser tab do not, so round them here.
    for y in range(size):
        t = y / max(size - 1, 1)
        draw.line(
            [(0, y), (size, y)],
            fill=tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)) + (255,),
        )

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(size * 0.22), fill=255
    )
    img.putalpha(mask)

    # Centre the glyph on its actual ink bounds, not the font's line box —
    # otherwise CJK glyphs sit visibly high.
    font = _font(round(size * 0.62))
    glyph = ImageDraw.Draw(img)
    left, top, right, bottom = glyph.textbbox((0, 0), GLYPH, font=font)
    glyph.text(
        ((size - (right - left)) / 2 - left, (size - (bottom - top)) / 2 - top),
        GLYPH,
        font=font,
        fill=(255, 255, 255, 255),
    )
    return img


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for size in (192, 512):
        path = os.path.join(OUT_DIR, f"icon-{size}.png")
        build(size).save(path, "PNG", optimize=True)
        print(f"wrote {os.path.relpath(path)} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
