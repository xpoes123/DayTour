#!/usr/bin/env python
"""Snapshot the itinerary page in two states: fresh, then with stops rejected."""

from playwright.sync_api import sync_playwright

URL = "https://daytour.djiang.xyz/itinerary/13"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1100, "height": 900})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.screenshot(path="/tmp/daytour-itin-fresh.png", full_page=True)

    # Reject 2 stops (positions 1 and 2) to trigger the recompute bar.
    remove_buttons = page.get_by_role("button", name="Remove stop").all()
    if len(remove_buttons) >= 2:
        remove_buttons[1].click()
        remove_buttons[2].click()
        page.wait_for_timeout(400)
        page.screenshot(path="/tmp/daytour-itin-rejected.png", full_page=True)
    browser.close()

print("/tmp/daytour-itin-fresh.png /tmp/daytour-itin-rejected.png")
