#!/usr/bin/env python3
"""Verify the white background fix - check rendering."""
from playwright.sync_api import sync_playwright
from PIL import Image

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    pg.goto("http://localhost:8080", wait_until="networkidle")

    # Accept disclaimer
    try:
        pg.click("#acceptDisclaimer", timeout=3000)
        pg.wait_for_timeout(500)
    except Exception:
        pass

    pg.screenshot(path="screenshots/verify_fix.png")
    b.close()

# Analyze
img = Image.open("screenshots/verify_fix.png").convert("RGB")
w, h = img.size
print(f"Screenshot: {w}x{h}")

points = {
    "navbar (10,10)": (10, 10),
    "hero center": (w // 2, h // 2),
    "hero left": (50, h // 2),
    "bottom": (w // 2, h - 10),
}
for name, (x, y) in points.items():
    px = img.getpixel((x, y))
    print(f"  {name}: RGB{px}")

hero = img.getpixel((w // 2, h // 2))
if hero[0] > 240 and hero[1] > 240 and hero[2] > 240:
    print("\nRESULT: HERO IS WHITE - STILL BROKEN")
else:
    print("\nRESULT: HERO HAS COLOR - RENDERING OK")

# Count white percentage
data = list(img.getdata())
white = sum(1 for p in data if p[0] > 245 and p[1] > 245 and p[2] > 245)
pct = 100 * white / len(data)
print(f"White pixels: {pct:.1f}%")
if pct > 90:
    print("PAGE IS MOSTLY WHITE - CSS NOT LOADING")
elif pct < 50:
    print("PAGE HAS CONTENT - CSS IS LOADING")
