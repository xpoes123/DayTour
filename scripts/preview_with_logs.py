#!/usr/bin/env python
"""Open a page, log any console errors, save a screenshot."""

import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://daytour.djiang.xyz/itinerary/17"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/daytour-debug.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    errors: list[str] = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type in {"error", "warning"} else None)
    page.on("pageerror", lambda exc: errors.append(f"[pageerror] {exc}"))
    page.goto(URL, wait_until="networkidle", timeout=20_000)
    page.wait_for_timeout(2000)
    page.screenshot(path=OUT, full_page=False)
    browser.close()

print(OUT)
for e in errors:
    print(e)
