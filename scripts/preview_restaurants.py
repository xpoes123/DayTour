#!/usr/bin/env python
"""Open an itinerary, expand 'Eat near here' on the first stop, screenshot."""

from playwright.sync_api import sync_playwright

URL = "https://daytour.djiang.xyz/itinerary/17"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 1100})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    buttons = page.get_by_role("button", name="Eat near here").all()
    if buttons:
        buttons[0].click()
        page.wait_for_timeout(2000)
    page.screenshot(path="/tmp/daytour-restaurants.png", full_page=True)
    browser.close()

print("/tmp/daytour-restaurants.png")
