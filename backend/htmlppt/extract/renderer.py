"""Render HTML in headless Chromium and capture a DOM snapshot.

The snapshot is a JSON tree with geometry (CSS px), computed styles, rich text
runs, tables, lists, SVG markup, image bytes and normalised chart data. It is
the only thing later pipeline stages see of the original HTML.
"""
from __future__ import annotations

import base64
import mimetypes
import tempfile
import urllib.parse
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

_JS_DIR = Path(__file__).parent
_SCRIPT = (_JS_DIR / "chart_probe.js").read_text(encoding="utf-8") + "\n" + \
          (_JS_DIR / "dom_snapshot.js").read_text(encoding="utf-8")


def snapshot_html(html: str | None = None, path: str | Path | None = None,
                  viewport: tuple[int, int] = (1920, 1080), timeout_ms: int = 20000) -> dict:
    """Render HTML (string or file) and return the DOM snapshot dict."""
    if html is None and path is None:
        raise ValueError("html or path required")
    tmp: Path | None = None
    if path is None:
        tmp = Path(tempfile.mkdtemp(prefix="htmlppt_")) / "input.html"
        tmp.write_text(html, encoding="utf-8")
        path = tmp
    url = Path(path).resolve().as_uri()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]}, device_scale_factor=1)
            try:
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            except Exception:
                page.wait_for_load_state("load", timeout=timeout_ms)
            page.add_script_tag(content=_SCRIPT)
            page.evaluate("() => document.fonts && document.fonts.ready")
            page.evaluate("window.__hpPrepare()")
            _scroll_through(page)
            page.wait_for_timeout(600)  # let charts/animations settle
            snap = page.evaluate("window.__hpSnapshot()")
            _resolve_assets(page, snap, Path(path).parent)
        finally:
            browser.close()
    snap["source"] = str(path)
    return snap


def _scroll_through(page: Page) -> None:
    """Scroll to trigger lazy-loading / reveal-on-scroll animations, then return to top."""
    page.evaluate("""async () => {
        const h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        for (let y = 0; y < h; y += Math.max(400, window.innerHeight * 0.8)) {
            window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40));
        }
        window.scrollTo(0, 0);
    }""")


def _iter_nodes(node: dict):
    yield node
    for k in node.get("kids", []) or []:
        yield from _iter_nodes(k)


def _resolve_assets(page: Page, snap: dict, base_dir: Path) -> None:
    """Attach image bytes (base64 + mime) to img/canvas/background-image nodes."""
    if not snap.get("root"):
        return
    for n in _iter_nodes(snap["root"]):
        src = None
        if n["tag"] in ("img", "canvas"):
            src = n.get("src")
        elif n.get("v", {}).get("bgUrl"):
            src = n["v"]["bgUrl"]
        if not src and n["tag"] == "canvas" and n.get("tainted"):
            try:
                png = page.locator(f'[data-hp-n="{n["id"]}"]').screenshot()
                n["img"] = {"mime": "image/png", "b64": base64.b64encode(png).decode()}
            except Exception:
                pass
            continue
        if not src:
            continue
        data = _load(page, src, base_dir)
        if data:
            n["img"] = {"mime": data[0], "b64": base64.b64encode(data[1]).decode()}
        n.pop("src", None)


def _load(page: Page, src: str, base_dir: Path) -> tuple[str, bytes] | None:
    try:
        if src.startswith("data:"):
            header, _, payload = src.partition(",")
            mime = header[5:].split(";")[0] or "image/png"
            raw = base64.b64decode(payload) if ";base64" in header else urllib.parse.unquote_to_bytes(payload)
            return mime, raw
        if src.startswith("file:"):
            p = Path(urllib.parse.unquote(urllib.parse.urlparse(src).path.lstrip("/")))
            if not p.exists():
                p = base_dir / p.name
            return (mimetypes.guess_type(p.name)[0] or "image/png"), p.read_bytes()
        if src.startswith("http"):
            r = page.request.get(src, timeout=10000)
            if r.ok:
                return (r.headers.get("content-type", "image/png").split(";")[0]), r.body()
    except Exception:
        return None
    return None
