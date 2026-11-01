"""Capture screenshots of key screens at multiple resolutions."""

import asyncio
import os
from playwright.async_api import async_playwright

RESOLUTIONS = [
    (375, 812, "phone"),
    (1024, 768, "tablet"),
    (1440, 900, "desktop"),
]

PAGES = [
    ("/", "login"),
    ("/game/", "world-map"),
]

BASE_URL = "http://localhost:8000"


async def capture_screenshots():
    """Capture screenshots at all resolutions."""
    os.makedirs("artifacts/screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for width, height, device in RESOLUTIONS:
            print(f"\n📸 {device} ({width}x{height})...")
            
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2,
            )
            page = await context.new_page()
            
            for path, name in PAGES:
                try:
                    await page.goto(f"{BASE_URL}{path}", timeout=10000)
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    await asyncio.sleep(0.5)
                    
                    filename = f"artifacts/screenshots/{name}-{device}.png"
                    await page.screenshot(path=filename, full_page=False)
                    print(f"  ✓ {name}")
                except Exception as e:
                    print(f"  ✗ {name}: {e}")
            
            await context.close()
        
        await browser.close()
    
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
