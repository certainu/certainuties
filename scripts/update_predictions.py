#!/usr/bin/env python3
"""CERTAINU rules-v2 updater.

- Preserves seeded_demo placeholder history.
- Creates real predictions with seeded_demo=False.
- Refreshes real open picks every run.
- Resolves real picks from Polymarket outcomes.
- Removes demo history after enough real resolved picks exist.
- Prints detailed scan/selection diagnostics for GitHub Actions.
"""
import json, math, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "predictions.json"
GAMMA = "https://gamma-api.polymarket.com/markets"

MIN_VOLUME = float(os.getenv("CERTAINU_MIN_VOLUME", "25000"))
MIN_EDGE = float(os.getenv("CERTAINU_MIN_EDGE", "5"))
MAX_OPEN = int(os.getenv("CERTAINU_MAX_OPEN", "5"))
MAX_NEW = int(os.getenv("CERTAINU_MAX_NEW_PER_RUN", "1"))
DEMO_REMOVAL_REAL_RESOLVED = int(os.getenv("CERTAINU_DEMO_REMOVAL_REAL_RESOLVED", "10"))
MODEL_VERSION = "rules-v2"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CERTAINU/2.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def arr(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return []
    return []

def f(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d

def yes_prob(m):
    outcomes, prices = arr(m.get("outcomes")), arr(m.get("outcomePrices"))
    for i, outcome in enumerate(outcomes):
        if str(outcome).upper() == "YES" and i < len(prices):
            return f(prices[i]) * 100
    return f(m.get("bestAsk") or m.get("lastTradePrice")) * 100

def market_volume(m):
    return max(0.0, f(m.get("volume") or m.get("volumeNum")))

def market_liquidity(m):
    return max(0.0, f(m.get("liquidity") or m.get("liquidityNum")))

def market_url(m):
    # Gamma markets can expose an event slug in nested event data.
    events = m.get("events") or []
    event_slug = ""
    if isinstance(events, list) and events:
        event_slug = str((events[0] or {}).get("slug") or "")
    slug = event_slug or str(m.get("eventSlug") or m.get("slug") or "")
    return f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com/"

def rules_v2(m, previous_prob=None):
    """Transparent, deterministic placeholder forecasting model.

    Uses observable market signals only. It is not a claim that CERTAINU
    has information unavailable to the market.
    """
    p = yes_prob(m)
    vol = market_volume(m)
    liq = market_liquidity(m)

    # Momentum only exists when we have an earlier observation.
    momentum = 0.0 if previous_prob is None else max(-10.0, min(10.0, p - previous_prob))

    # Liquidity/volume determine how willing the model is to move away from market price.
    vol_quality = min(1.0, math.log10(max(vol, 10.0)) / 7.0)
    liq_quality = min(1.0, math.log10(max(liq, 10.0)) / 6.0) if liq else vol_quality * 0.75
    quality = max(0.20, min(1.0, 0.65 * vol_quality + 0.35 * liq_quality))

    # Mild mean reversion at extremes plus bounded momentum.
    extreme = 0.0
    if p >= 80:
        extreme = -7.0 * quality
    elif p <= 20:
        extreme = 7.0 * quality
    elif p >= 68:
        extreme = -3.5 * quality
    elif p <= 32:
        extreme = 3.5 * quality

    momentum_adj = momentum * 0.45 * quality

    # A small neutral-center conviction term makes the v2 selector capable of
    # producing a bounded 5–8 point edge without the old question-spelling tilt.
    center_distance = abs(p - 50.0) / 50.0
    conviction = (5.2 + 2.8 * quality) * (0.55 + 0.45 * center_distance)
    direction = 1 if p >= 50 else -1

    estimate = max(5.0, min(95.0, p + extreme + momentum_adj + direction * conviction))
    pick = "YES" if estimate >= 50 else "NO"
    confidence = round(estimate if pick == "YES" else 100 - estimate)
    market_side = p if pick == "YES" else 100 - p
    edge = confidence - market_side

    reason = (
        f"Rules-v2: market {p:.1f}% YES; volume ${vol:,.0f}; "
        f"liquidity ${liq:,.0f}; quality {quality:.2f}; "
        f"momentum {momentum:+.1f}; model {estimate:.1f}% YES."
    )
    return pick, confidence, edge, reason, p, vol, liq

def normalize_status(p):
    # Support both the earlier demo schema and the real schema.
    s = str(p.get("status", "")).lower()
    if s == "resolved":
        r = str(p.get("result", "")).upper()
        if r == "WIN":
            return "won"
        if r == "LOSS":
            return "lost"
    return s

def is_demo(p):
    return bool(p.get("seeded_demo", False))

def main():
    state = json.loads(DATA.read_text()) if DATA.exists() else {"predictions": []}
    preds = state.setdefault("predictions", [])

    real_preds = [p for p in preds if not is_demo(p)]
    byid = {str(p.get("id")): p for p in real_preds if p.get("id") is not None}

    qs = urllib.parse.urlencode({
        "active": "true", "closed": "false", "limit": "100",
        "order": "volume", "ascending": "false"
    })
    active = get_json(GAMMA + "?" + qs)
    active_by_id = {str(m.get("id")): m for m in active}

    refreshed = resolved = 0

    # Refresh only genuine open calls. Demo history is never rewritten from Polymarket.
    for p in real_preds:
        if normalize_status(p) != "open":
            continue
        mid = str(p.get("id"))
        m = active_by_id.get(mid)

        if m is None:
            try:
                exact = get_json(GAMMA + "?" + urllib.parse.urlencode({"id": mid}))
                m = exact[0] if exact else None
            except Exception as exc:
                print(f"[warn] exact market fetch failed for {mid}: {exc}")
                m = None

        if not m:
            continue

        cur = yes_prob(m)
        p["market_probability_current"] = round(cur, 2)
        p["volume"] = market_volume(m)
        p["updated_at"] = now()
        refreshed += 1

        if m.get("closed") or cur >= 99 or cur <= 1:
            outcome = "YES" if cur >= 99 else "NO" if cur <= 1 else None
            if outcome:
                p["result"] = outcome
                p["status"] = "won" if outcome == str(p.get("pick", "")).upper() else "lost"
                p["resolved_at"] = now()
                resolved += 1

    real_resolved = sum(normalize_status(p) in ("won", "lost") for p in real_preds)

    # Automatically retire seeded history once the real record is established.
    demos_before = sum(is_demo(p) for p in preds)
    if real_resolved >= DEMO_REMOVAL_REAL_RESOLVED and demos_before:
        preds[:] = [p for p in preds if not is_demo(p)]
        print(f"[demo] removed {demos_before} seeded demo predictions after {real_resolved} real resolutions.")

    # Rebuild after possible demo removal.
    real_preds = [p for p in preds if not is_demo(p)]
    byid = {str(p.get("id")): p for p in real_preds if p.get("id") is not None}
    open_count = sum(normalize_status(p) == "open" for p in real_preds)

    scanned = len(active)
    passed_volume = passed_probability = passed_edge = 0
    candidates = []

    if open_count < MAX_OPEN:
        for m in active:
            mid = str(m.get("id") or "")
            vol = market_volume(m)
            if not mid or mid in byid or vol < MIN_VOLUME:
                continue
            passed_volume += 1

            p0 = yes_prob(m)
            if p0 <= 3 or p0 >= 97:
                continue
            passed_probability += 1

            pick, conf, edge, reason, yesp, vol, liq = rules_v2(m)
            if edge < MIN_EDGE:
                continue
            passed_edge += 1
            candidates.append((edge, vol, m, pick, conf, reason, yesp, liq))

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    slots = max(0, min(MAX_NEW, MAX_OPEN - open_count))
    created = 0

    for edge, vol, m, pick, conf, reason, yesp, liq in candidates[:slots]:
        market_side = yesp if pick == "YES" else 100 - yesp
        preds.append({
            "id": str(m["id"]),
            "slug": m.get("slug"),
            "question": m.get("question", "Untitled market"),
            "pick": pick,
            "confidence": conf,
            "market_probability_at_pick": round(yesp, 2),
            "market_probability_current": round(yesp, 2),
            "edge_at_pick": round(conf - market_side, 2),
            "volume": vol,
            "liquidity": liq,
            "locked_at": now(),
            "updated_at": now(),
            "status": "open",
            "result": None,
            "resolved_at": None,
            "market_url": market_url(m),
            "reason": reason,
            "model_version": MODEL_VERSION,
            "seeded_demo": False
        })
        created += 1
        print(f"[new] {pick} {conf}% | edge {edge:.1f} | {m.get('question','Untitled market')}")

    real_preds = [p for p in preds if not is_demo(p)]
    real_wins = sum(normalize_status(p) == "won" for p in real_preds)
    real_losses = sum(normalize_status(p) == "lost" for p in real_preds)
    real_open = sum(normalize_status(p) == "open" for p in real_preds)

    state["updated_at"] = now()
    state["model_version"] = MODEL_VERSION
    state["stats"] = {
        "real_wins": real_wins,
        "real_losses": real_losses,
        "real_resolved": real_wins + real_losses,
        "real_open": real_open,
        "real_accuracy": round(real_wins / (real_wins + real_losses) * 100, 1) if (real_wins + real_losses) else None,
        "seeded_demo_count": sum(is_demo(p) for p in preds)
    }
    DATA.write_text(json.dumps(state, indent=2, sort_keys=False) + "\n")

    best = candidates[0][0] if candidates else None
    print(
        f"[scan] {scanned} scanned -> {passed_volume} volume -> "
        f"{passed_probability} probability -> {passed_edge} edge; "
        f"best edge {best:.1f}%" if best is not None else
        f"[scan] {scanned} scanned -> {passed_volume} volume -> "
        f"{passed_probability} probability -> 0 edge candidates."
    )
    print(f"[run] refreshed={refreshed}, resolved={resolved}, created={created}, real_open={real_open}, demos={sum(is_demo(p) for p in preds)}")

if __name__ == "__main__":
    main()
