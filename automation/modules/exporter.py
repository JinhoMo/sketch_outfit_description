"""Render HTML to PNG / PDF using headless Chromium (Playwright).

Runs Playwright in a dedicated subprocess to avoid Windows asyncio
SelectorEventLoop issues under Streamlit.
"""
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger("sketch.exporter")

WORKER = Path(__file__).parent / "exporter_worker.py"
_CHROMIUM_READY = False


def _ensure_chromium() -> None:
    global _CHROMIUM_READY
    if _CHROMIUM_READY:
        return
    # If system chromium exists, skip download
    for p in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium"):
        if os.path.exists(p):
            _CHROMIUM_READY = True
            return
    logger.info("installing playwright chromium...")
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        logger.error("playwright install failed: %s", r.stderr)
        raise RuntimeError(f"playwright install failed: {r.stderr}")
    _CHROMIUM_READY = True


def _render(html: str, mode: str) -> bytes:
    _ensure_chromium()
    with tempfile.TemporaryDirectory() as d:
        html_path = Path(d) / "in.html"
        out_path = Path(d) / ("out.pdf" if mode == "pdf" else "out.png")
        html_path.write_text(html, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(WORKER), mode, str(html_path), str(out_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            logger.error("exporter worker failed: %s", result.stderr)
            raise RuntimeError(result.stderr.strip() or "exporter worker failed")
        return out_path.read_bytes()


def html_to_pdf(html: str) -> bytes:
    logger.info("html -> pdf")
    return _render(html, "pdf")


def html_to_png(html: str) -> bytes:
    logger.info("html -> png")
    return _render(html, "png")
