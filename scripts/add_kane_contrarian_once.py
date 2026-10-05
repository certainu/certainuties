#!/usr/bin/env python3
"""Add exactly one Harry Kane 2026 Ballon d'Or contrarian prediction.

This is intentionally a contrarian call: CERTAINU takes the opposite side of the
current Polymarket majority at insertion time. The record is labeled `contrarian`
so it is distinguishable from normal automated model picks. This script does not
modify the hourly updater and locks itself after a successful run.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "predictions.json"
GAMMA = "https://gamma-api.polymarket.com/markets"
MARKER = "kane_ballon_dor_contrarian_2026_once"
TARGET_PHRASES = ("harry kane", "ballon d'or")


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CERTAINU/2.1", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def as_array(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return []
    return []


def yes_probability(market):
    outcomes = as_array(market.get("outcomes"))
    prices = as_array(market.get("outcomePrices"))
    for i, outcome in enumerate(outcomes):
        if str(outcome).strip().upper() == "YES" and i < len(prices):
            return float(prices[i]) * 100
    raise RuntimeError("Could not determine the live YES probability for the Kane market.")


def number(market, *keys):
    for key in keys:
        value = market.get(key)
        if value not in (None, ""):
            try:
                return float(str(value).replace(",", "").replace("$", "").strip())
            except Exception:
                pass
    return 0.0


def find_kane_market():
    matches = []
    for offset in range(0, 5000, 100):
        query = urllib.parse.urlencode({"active": "true", "closed": "false", "limit": 100, "offset": offset})
        page = get_json(GAMMA + "?" + query)
        if not page:
            break
        for market in page:
            text = " ".join(str(market.get(k) or "") for k in ("question", "slug", "description")).lower()
            if all(phrase in text for phrase in TARGET_PHRASES):
                matches.append(market)
        if len(page) < 100:
            break
    if not matches:
        raise SystemExit("No active Harry Kane 2026 Ballon d'Or market was found; nothing changed.")
    # Prefer the exact YES/NO market if more than one related market is returned.
    matches.sort(key=lambda m: ("will-harry-kane" not in str(m.get("slug", "")).lower(), str(m.get("id", ""))))
    return matches[0]


def market_url(market):
    events = market.get("events") or []
    event_slug = ""
    if isinstance(events, list) and events:
        event_slug = str((events[0] or {}).get("slug") or "")
    slug = event_slug or str(market.get("eventSlug") or market.get("slug") or "")
    return f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com/"


def main():
    state = json.loads(DATA.read_text(encoding="utf-8"))
    if state.get(MARKER):
        raise SystemExit("Already completed: the Kane contrarian call will not be added twice.")

    predictions = state.setdefault("predictions", [])
    market = find_kane_market()
    market_id = str(market.get("id"))

    if any(str(p.get("id")) == market_id and str(p.get("status", "")).lower() == "open" for p in predictions):
        raise SystemExit("The Harry Kane market is already present as an open CERTAINU prediction; nothing changed.")

    open_count = sum(str(p.get("status", "")).lower() == "open" for p in predictions if not p.get("seeded_demo", False))
    if open_count >= 100:
        raise SystemExit(f"Refusing to exceed the 100-open-prediction cap ({open_count} currently open).")

    yes = yes_probability(market)
    if yes == 50:
        raise SystemExit("Polymarket is exactly 50/50 right now, so there is no majority side to oppose; nothing changed.")

    pick = "YES" if yes < 50 else "NO"
    majority = "NO" if yes < 50 else "YES"
    confidence = round(max(51, min(95, 100 - yes if pick == "NO" else yes)))
    # Contrarian confidence is deliberately kept modest: this is not a normal model-derived confidence score.
    confidence = 55
    volume = number(market, "volumeNum", "volume", "volumeClob", "volume24hr")
    liquidity = number(market, "liquidityNum", "liquidity", "liquidityClob")
    stamp = now()
    end_date = market.get("endDate") or market.get("end_date") or market.get("endDateIso") or market.get("endDateISO")

    record = {
        "id": market_id,
        "slug": market.get("slug"),
        "question": market.get("question", "Will Harry Kane win the 2026 Ballon d'Or?"),
        "pick": pick,
        "confidence": confidence,
        "market_probability_at_pick": round(yes, 2),
        "market_probability_current": round(yes, 2),
        "edge_at_pick": round((confidence - yes) if pick == "YES" else (confidence - (100 - yes)), 2),
        "selection_score": 0,
        "market_end_date": end_date,
        "volume": volume,
        "liquidity": liquidity,
        "locked_at": stamp,
        "updated_at": stamp,
        "status": "open",
        "result": None,
        "resolved_at": None,
        "market_url": market_url(market),
        "reason": f"Contrarian call: Polymarket was {yes:.1f}% YES / {100-yes:.1f}% NO at lock. CERTAINU took the opposite side of the market majority ({majority}).",
        "model_version": "contrarian",
        "category": "sports",
        "label": "contrarian",
        "contrarian": True,
        "seeded_demo": False
    }
    predictions.append(record)
    state[MARKER] = {"completed_at": stamp, "market_id": market_id, "pick": pick, "market_yes_at_lock": round(yes, 2)}
    state["updated_at"] = stamp
    DATA.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    print(f"Added Kane contrarian prediction: {pick}")
    print(f"Polymarket at lock: {yes:.1f}% YES / {100-yes:.1f}% NO")
    print("Record label: contrarian")
    print("Done. This script is locked against adding the call again.")


if __name__ == "__main__":
    main()
