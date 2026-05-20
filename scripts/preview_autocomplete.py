#!/usr/bin/env python
"""Type into the planner's starting-location field and screenshot the dropdown."""

from playwright.sync_api import sync_playwright

URL = "https://daytour.djiang.xyz/plan"
OUT = "/tmp/daytour-autocomplete.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 900, "height": 700})
    page.goto(URL, wait_until="networkidle")
    field = page.get_by_role("combobox", name="Starting location")
    field.click()
    field.fill("wisconsin state cap")
    # Wait for debounce + network
    page.wait_for_timeout(900)
    page.screenshot(path=OUT, full_page=False)
    browser.close()

print(OUT)
