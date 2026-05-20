#!/usr/bin/env python
"""Headless Chromium screenshot of a DayTour page.

Usage:
    .venv/bin/python scripts/preview.py [url] [out_path]

Defaults: https://daytour.djiang.xyz/ → /tmp/daytour-preview.png

Used during iteration so I don't have to ask David to screenshot every change.
Modeled on code/games/scripts/preview.py.
"""

from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://daytour.djiang.xyz/"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/daytour-preview.png"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 800})
        page.goto(url, wait_until="networkidle", timeout=20_000)
        # Settle map tiles / lazy chunks
        page.wait_for_timeout(1200)
        page.screenshot(path=out, full_page=True)
        browser.close()

    print(out)


if __name__ == "__main__":
    main()
