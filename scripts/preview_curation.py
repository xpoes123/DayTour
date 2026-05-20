#!/usr/bin/env python
"""Open an itinerary, X a stop, screenshot the alternatives picker."""

from playwright.sync_api import sync_playwright

# A walking itinerary with several stops we can curate.
URL = "https://daytour.djiang.xyz/itinerary/7"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 1000})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)

    # X the third stop (skip the anchor at 0) to trigger the picker.
    remove_buttons = page.get_by_role("button", name="Remove stop").all()
    if len(remove_buttons) >= 3:
        remove_buttons[2].click()
        # Wait for alternatives + photo bytes to fully load.
        page.wait_for_timeout(4500)
    page.screenshot(path="/tmp/daytour-curation.png", full_page=True)
    browser.close()

print("/tmp/daytour-curation.png")
