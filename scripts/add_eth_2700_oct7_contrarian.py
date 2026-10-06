#!/usr/bin/env python3
"""One-time, idempotent add for CERTAINU's ETH > $2,700 Oct. 7 contrarian call.

This script ONLY edits data/predictions.json. It does not touch index.html,
filters, CSS, JavaScript, or the normal updater.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "predictions.json"
GAMMA = "https://gamma-api.polymarket.com/markets"
TARGET_SLUG = "ethereum-above-2700-on-october-7-2026"
EXPECTED_END_PREFIX = "2026-10-07"
PICK = "NO"
CONFIDENCE = 54
MODEL_VERSION = "manual-contrarian-eth2700-oct7-v1"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CERTAINU/2.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def arr(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return []
    return []

def f(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def yes_prob(market):
    outcomes = arr(market.get("outcomes"))
    prices = arr(market.get("outcomePrices"))
    for i, outcome in enumerate(outcomes):
        if str(outcome).upper() == "YES" and i < len(prices):
            return f(prices[i]) * 100
    return f(market.get("bestAsk") or market.get("lastTradePrice")) * 100

def num(market, keys):
    for key in keys:
        value = market.get(key)
        if value in (None, ""):
            continue
        try:
            return float(str(value).replace(",", "").replace("$", "").strip())
        except Exception:
            pass
    return 0.0

def volume(market):
    return max(0.0, num(market, (
        "volumeNum", "volume", "volumeClob", "volume24hr",
        "volume1wk", "volume1mo", "volume1yr",
    )))

def liquidity(market):
    return max(0.0, num(market, ("liquidityNum", "liquidity", "liquidityClob")))

def status(prediction):
    s = str(prediction.get("status", "")).lower()
    if s == "resolved":
        result = str(prediction.get("result", "")).upper()
        return "won" if result == "WIN" else "lost" if result == "LOSS" else s
    return s

def is_demo(prediction):
    return bool(prediction.get("seeded_demo", False))

def main():
    if not DATA.exists():
        raise SystemExit("ERROR: data/predictions.json not found")

    state = json.loads(DATA.read_text(encoding="utf-8"))
    predictions = state.setdefault("predictions", [])

    # Idempotency: rerunning this script can never add a second copy.
    if any(
        str(p.get("slug") or "") == TARGET_SLUG
        or str(p.get("manual_key") or "") == "eth2700-oct7-contrarian"
        for p in predictions
    ):
        print("ETH > $2,700 Oct. 7 contrarian call already exists; nothing changed.")
        return

    query = urllib.parse.urlencode({"slug": TARGET_SLUG})
    markets = get_json(GAMMA + "?" + query)
    if not markets:
        raise SystemExit("ERROR: target Polymarket market was not found")

    market = markets[0]
    slug = str(market.get("slug") or "")
    question = str(market.get("question") or "")
    end_date = str(
        market.get("endDate") or market.get("end_date")
        or market.get("endDateIso") or market.get("endDateISO") or ""
    )

    # Safety checks ensure a similarly named market cannot be inserted by mistake.
    if slug != TARGET_SLUG:
        raise SystemExit(f"ERROR: wrong market returned: {slug}")
    if "ethereum" not in question.lower() or "2,700" not in question.replace("$", ""):
        raise SystemExit(f"ERROR: unexpected target question: {question}")
    if end_date and not end_date.startswith(EXPECTED_END_PREFIX):
        raise SystemExit(f"ERROR: unexpected market end date: {end_date}")
    if market.get("closed"):
        raise SystemExit("ERROR: target market is already closed")

    yesp = round(yes_prob(market), 2)
    if not 40 <= yesp <= 60:
        raise SystemExit(
            f"ERROR: market is no longer close enough to 50/50 ({yesp:.2f}% YES); "
            "prediction was not added"
        )

    # This is specifically a contrarian NO call. Require the market to be on the
    # YES side at lock so CERTAINU is actually disagreeing with Polymarket.
    if yesp < 50:
        raise SystemExit(
            f"ERROR: Polymarket currently favors NO ({yesp:.2f}% YES); "
            "CERTAINU's NO would no longer be contrarian"
        )

    locked = now()
    no_market_probability = 100 - yesp
    event_slug = ""
    events = market.get("events") or []
    if isinstance(events, list) and events:
        event_slug = str((events[0] or {}).get("slug") or "")
    market_url = (
        f"https://polymarket.com/event/{event_slug or 'ethereum-above-on-october-7-2026'}"
        f"?marketSlug={TARGET_SLUG}"
    )

    prediction = {
        "id": str(market.get("id") or ""),
        "slug": TARGET_SLUG,
        "question": question,
        "pick": PICK,
        "confidence": CONFIDENCE,
        "market_probability_at_pick": yesp,
        "market_probability_current": yesp,
        "edge_at_pick": round(CONFIDENCE - no_market_probability, 2),
        "selection_score": None,
        "hours_to_resolution_at_pick": None,
        "market_end_date": end_date or "2026-10-07T00:00:00Z",
        "volume": volume(market),
        "liquidity": liquidity(market),
        "locked_at": locked,
        "updated_at": locked,
        "status": "open",
        "result": None,
        "resolved_at": None,
        "market_url": market_url,
        "reason": (
            f"Contrarian call: Polymarket was {yesp:.1f}% YES / "
            f"{100-yesp:.1f}% NO at lock; CERTAINU takes NO at "
            f"{CONFIDENCE}% confidence."
        ),
        "model_version": MODEL_VERSION,
        "category": "crypto",
        "seeded_demo": False,
        "contrarian": True,
        "manual_key": "eth2700-oct7-contrarian",
    }

    if not prediction["id"]:
        raise SystemExit("ERROR: target market has no market ID")

    # Put the new call first, matching the site's newest-first data convention.
    predictions.insert(0, prediction)

    # Recompute the same top-level stats used by the normal updater.
    real = [p for p in predictions if not is_demo(p)]
    wins = sum(status(p) == "won" for p in real)
    losses = sum(status(p) == "lost" for p in real)
    open_count = sum(status(p) == "open" for p in real)
    stats = state.setdefault("stats", {})
    stats.update({
        "real_wins": wins,
        "real_losses": losses,
        "real_resolved": wins + losses,
        "real_open": open_count,
        "real_accuracy": round(wins / (wins + losses) * 100, 1)
        if wins + losses else None,
        "seeded_demo_count": sum(is_demo(p) for p in predictions),
        "visible_predictions": len(predictions),
        "crypto_open": sum(
            status(p) == "open" and str(p.get("category", "")).lower() == "crypto"
            for p in real
        ),
    })
    state["updated_at"] = locked

    DATA.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(
        f"Added: {question} | CERTAINU {PICK} {CONFIDENCE}% | "
        f"market at lock {yesp:.2f}% YES / {100-yesp:.2f}% NO"
    )

if __name__ == "__main__":
    main()
