#!/usr/bin/env python
"""Open an itinerary, click the Share button, screenshot the dropdown."""

from playwright.sync_api import sync_playwright

URL = "https://daytour.djiang.xyz/itinerary/17"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Share").click()
    page.wait_for_timeout(400)
    page.screenshot(path="/tmp/daytour-share-menu.png", full_page=False)
    browser.close()

print("/tmp/daytour-share-menu.png")
