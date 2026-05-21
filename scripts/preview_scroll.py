#!/usr/bin/env python
"""Snapshot the itinerary at top-of-page and after scrolling halfway down to
prove the map stays in view."""

from playwright.sync_api import sync_playwright

URL = "https://daytour.djiang.xyz/itinerary/17"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.screenshot(path="/tmp/daytour-scroll-top.png", full_page=False)
    # Scroll past the first two stops.
    page.evaluate("window.scrollTo(0, 700)")
    page.wait_for_timeout(600)
    page.screenshot(path="/tmp/daytour-scroll-mid.png", full_page=False)
    browser.close()

print("/tmp/daytour-scroll-top.png /tmp/daytour-scroll-mid.png")
