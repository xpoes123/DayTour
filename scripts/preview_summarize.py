#!/usr/bin/env python
"""Click the Summarize my day button, screenshot after it resolves."""

import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://daytour.djiang.xyz/itinerary/22"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    btn = page.get_by_role("button", name="Summarize my day")
    if btn.count():
        btn.click()
        # Wait for Claude.
        page.wait_for_timeout(8000)
    page.screenshot(path="/tmp/daytour-summarized.png", full_page=False)
    browser.close()

print("/tmp/daytour-summarized.png")
