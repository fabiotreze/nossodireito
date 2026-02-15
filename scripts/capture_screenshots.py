#!/usr/bin/env python3
"""Capture screenshots of the running site for validation."""

from playwright.sync_api import sync_playwright
import os

SCREENSHOTS_DIR = "screenshots"
BASE_URL = "http://localhost:8080"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def capture(page, name, description=""):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.screenshot(path=path)
    size_kb = os.path.getsize(path) / 1024
    print(f"  {name} ({size_kb:.0f} KB) - {description}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- Desktop ---
        print("\n=== Desktop (1280x800) ===")
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="networkidle")

        # Dismiss disclaimer modal if present
        try:
            page.click("#acceptDisclaimer", timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        capture(page, "01_hero_desktop.png", "Hero section")

        page.evaluate('document.querySelector("#busca").scrollIntoView()')
        page.wait_for_timeout(300)
        capture(page, "02_busca_desktop.png", "Search section")

        page.evaluate('document.querySelector("#categorias").scrollIntoView()')
        page.wait_for_timeout(300)
        capture(page, "03_categorias_desktop.png", "Categories section")

        page.evaluate('document.querySelector("footer.footer").scrollIntoView({block:"end",behavior:"instant"})')
        page.wait_for_timeout(500)
        capture(page, "04_footer_desktop.png", "Footer")

        # Full page
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        capture(page, "05_fullpage_desktop.png", "Full page (top)")

        ctx.close()

        # --- Mobile ---
        print("\n=== Mobile (375x812 @2x) ===")
        ctx = browser.new_context(
            viewport={"width": 375, "height": 812},
            device_scale_factor=2,
        )
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="networkidle")

        try:
            page.click("#acceptDisclaimer", timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        capture(page, "06_hero_mobile.png", "Hero section")

        page.evaluate('document.querySelector("#categorias").scrollIntoView()')
        page.wait_for_timeout(300)
        capture(page, "07_categorias_mobile.png", "Categories section")

        page.evaluate('document.querySelector("footer.footer").scrollIntoView({block:"end",behavior:"instant"})')
        page.wait_for_timeout(500)
        capture(page, "08_footer_mobile.png", "Footer")

        ctx.close()

        # --- Dark Mode ---
        print("\n=== Dark Mode Desktop (1280x800) ===")
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            color_scheme="dark",
        )
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="networkidle")

        try:
            page.click("#acceptDisclaimer", timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        capture(page, "09_hero_dark.png", "Hero section (dark mode)")

        page.evaluate('document.querySelector("#categorias").scrollIntoView()')
        page.wait_for_timeout(300)
        capture(page, "10_categorias_dark.png", "Categories (dark mode)")

        ctx.close()
        browser.close()

    print("\nAll screenshots saved to screenshots/")


if __name__ == "__main__":
    main()
