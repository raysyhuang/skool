"""Capture screenshots of key screens at multiple resolutions."""

import asyncio
import os
from playwright.async_api import async_playwright

RESOLUTIONS = [
    (375, 812, "phone"),       # iPhone X/11/12/13
    (1024, 768, "tablet"),     # iPad landscape
    (1440, 900, "desktop"),    # MacBook Pro
]

PAGES = [
    ("/", "login"),
    ("/game/", "world-map"),
    ("/game/daily-quests", "daily-quests"),
    ("/game/garage", "garage"),
    ("/game/journey", "journey-map"),
]

BASE_URL = "http://localhost:8000"


async def capture_screenshots():
    """Capture screenshots at all resolutions."""
    os.makedirs("/workspace/artifacts/screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for width, height, device in RESOLUTIONS:
            print(f"\n📸 Capturing {device} ({width}x{height})...")
            
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2,
            )
            page = await context.new_page()
            
            # Login first
            await page.goto(f"{BASE_URL}/")
            await page.wait_for_load_state("networkidle")
            
            # Click first kid avatar if exists
            try:
                await page.click(".avatar-card", timeout=2000)
                await page.wait_for_load_state("networkidle")
            except:
                print("  ℹ️  No login needed or already logged in")
            
            # Capture each page
            for path, name in PAGES:
                try:
                    await page.goto(f"{BASE_URL}{path}")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(1)  # Let animations settle
                    
                    filename = f"/workspace/artifacts/screenshots/{name}-{device}.png"
                    await page.screenshot(path=filename, full_page=False)
                    print(f"  ✓ {name}")
                except Exception as e:
                    print(f"  ✗ {name}: {e}")
            
            await context.close()
        
        await browser.close()
    
    print("\n✅ All screenshots captured!")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
