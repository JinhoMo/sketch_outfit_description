"""Playwright worker: invoked as subprocess by exporter.py.

Usage: python exporter_worker.py <pdf|png> <input.html> <output-path>
"""
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright


def main():
    mode, in_path, out_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    html = in_path.read_text(encoding="utf-8")
    import os
    system_chromium = None
    for candidate in ("/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if os.path.exists(candidate):
            system_chromium = candidate
            break
    with sync_playwright() as p:
        launch_kwargs = {}
        if system_chromium:
            launch_kwargs["executable_path"] = system_chromium
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(viewport={"width": 960, "height": 1400},
                                  device_scale_factor=2)
        page = ctx.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(600)
        if mode == "pdf":
            data = page.pdf(format="A4", print_background=True,
                            margin={"top": "12mm", "bottom": "12mm",
                                    "left": "10mm", "right": "10mm"})
        else:
            data = page.locator(".page").screenshot(type="png", omit_background=False)
        out_path.write_bytes(data)
        browser.close()


if __name__ == "__main__":
    main()
