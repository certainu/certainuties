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
            # All predictions excludes resolved results, and starts collapsed.
            page.wait_for_function(
                "() => document.querySelectorAll('#predictionList .prediction-card:not([style*=\\\"display: none\\\"])').length >= 5",
                timeout=10000,
            )
            assert page.locator("#predictionList .prediction-card").count() == 12
            assert page.locator("#predictionList .prediction-card[data-resolution-bucket='resolved']").count() == 7
            assert page.locator("#predictionList .prediction-card[data-resolution-bucket='resolved']:visible").count() == 0
            page.locator("#predictionExpandBtn").click()
            assert page.locator("#predictionExpandBtn").get_attribute("aria-expanded") == "true"
            page.locator("#predictionExpandBtn").click()
            assert page.locator("#predictionExpandBtn").get_attribute("aria-expanded") == "false"
            page.locator("#predictionTimeFilters [data-filter='resolved']").click()
            assert page.locator("#predictionList .prediction-card[data-resolution-bucket='resolved']:visible").count() >= 3
            page.locator("#predictionTimeFilters [data-filter='all']").click()
            # Receipts have seven resolved entries; the expander must work.
            page.locator("#receiptsExpandBtn").click()
            assert page.locator("#receiptsExpandBtn").get_attribute("aria-expanded") == "true"
            page.locator("#receiptsExpandBtn").click()
            assert page.locator("#receiptsExpandBtn").get_attribute("aria-expanded") == "false"
            # At equal probabilities, badge rectangles must not overlap.
            badges = page.locator("#markets .yn-now-marker em, #markets .yn-lock-marker em")
            assert badges.count() >= 2
            now = page.locator("#markets .yn-now-marker em").first.bounding_box()
            lock = page.locator("#markets .yn-lock-marker em").first.bounding_box()
            assert now and lock
            vertical_overlap = min(now["y"]+now["height"], lock["y"]+lock["height"]) - max(now["y"], lock["y"])
            assert vertical_overlap <= 0, f"Market badges overlap vertically: {vertical_overlap}"
            screenshots = ROOT / "test-artifacts"
            screenshots.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshots / f"site-{width}.png"), full_page=True)
            assert not errors, f"Browser JavaScript errors: {errors}"
            print(f"Chromium {width}px: prediction cards, receipts and markers rendered")
            page.close()
        browser.close()
finally:
    server.shutdown()
