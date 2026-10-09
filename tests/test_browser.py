#!/usr/bin/env python3
"""Real Chromium smoke test against a deterministic prediction feed."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

fixture = {"updated_at": "2026-10-08T20:00:00Z", "model_version": "browser-smoke-test", "predictions": []}
for i in range(12):
    resolved = i >= 5
    fixture["predictions"].append({
        "id": f"test-{i}", "question": f"Browser smoke market {i}",
        "pick": "YES" if i % 2 else "NO", "confidence": 75,
        "market_probability_at_pick": 60, "market_probability_current": 60,
        "status": "won" if resolved else "open",
        "result": "WIN" if resolved else None,
        "category": "sports", "locked_at": "2026-10-08T18:00:00Z",
        "resolved_at": "2026-10-08T19:00:00Z" if resolved else None,
        "market_end_date": "2026-10-10T00:00:00Z",
        "market_url": "https://polymarket.com/"
    })

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width in (1280, 390):
            page = browser.new_page(viewport={"width": width, "height": 850})
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            def intercept(route):
                url = route.request.url
                if "/data/predictions.json" in url:
                    route.fulfill(status=200, content_type="application/json", body=json.dumps(fixture))
                elif url.startswith(f"http://127.0.0.1:{server.server_port}/"):
                    route.continue_()
                else:
                    route.abort()
            page.route("**/*", intercept)
            page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="domcontentloaded")
            page.locator("#predictionList .prediction-card").first.wait_for(timeout=20000)
            page.wait_for_function("document.querySelectorAll('#predictionList .prediction-card').length >= 12", timeout=20000)
            assert page.locator("#receiptsLedger .receipts-row").count() >= 8, "Receipts did not render"
            assert page.locator("#markets .yn-lock-marker").count() > 0, "Lock markers missing"
            assert page.locator("#markets .yn-now-marker").count() > 0, "Current markers missing"
            assert page.locator("#predictionExpandBtn").count() == 1, "Prediction expander missing"
            assert not errors, f"Browser JavaScript errors: {errors}"
            print(f"Chromium {width}px: prediction cards, receipts and markers rendered")
            page.close()
        browser.close()
finally:
    server.shutdown()
