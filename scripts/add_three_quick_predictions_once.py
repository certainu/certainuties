#!/usr/bin/env python3
"""One-time helper: append exactly 3 qualifying Polymarket calls resolving within 24h.

Run manually once with:
    python scripts/add_three_quick_predictions_once.py

This does NOT change the normal hourly updater. It refuses to run a second time after
success by recording a marker in data/predictions.json.
"""
import json, math, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "predictions.json"
GAMMA = "https://gamma-api.polymarket.com/markets"
MARKER = "manual_three_quick_predictions_2026_10_05"
MIN_VOLUME = 5000.0
COUNT = 3


def now_dt():
    return datetime.now(timezone.utc)


def now():
    return now_dt().isoformat().replace("+00:00", "Z")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CERTAINU/2.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def arr(v):
    if isinstance(v, list): return v
    if isinstance(v, str):
        try: return json.loads(v)
        except Exception: return []
    return []


def f(v, d=0.0):
    try: return float(v)
    except Exception: return d


def yes_prob(m):
    outcomes, prices = arr(m.get("outcomes")), arr(m.get("outcomePrices"))
    for i, outcome in enumerate(outcomes):
        if str(outcome).upper() == "YES" and i < len(prices):
            return f(prices[i]) * 100
    return f(m.get("bestAsk") or m.get("lastTradePrice")) * 100


def num(m, keys):
    for k in keys:
        v = m.get(k)
        if v in (None, ""): continue
        try: return float(str(v).replace(",", "").replace("$", "").strip())
        except Exception: pass
    return 0.0


def volume(m):
    return max(0, num(m, ("volumeNum", "volume", "volumeClob", "volume24hr", "volume1wk", "volume1mo", "volume1yr")))


def liquidity(m):
    return max(0, num(m, ("liquidityNum", "liquidity", "liquidityClob")))


def parse_end(m):
    raw = m.get("endDate") or m.get("end_date") or m.get("endDateIso") or m.get("endDateISO")
    if not raw: return None
    try: return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception: return None


def hours_left(m):
    e = parse_end(m)
    return (e - now_dt()).total_seconds() / 3600 if e else None


def crypto_market(x):
    text = " ".join(str(x.get(k) or "") for k in ("question", "slug", "eventSlug", "description")).lower()
    ev = x.get("events") or []
    if isinstance(ev, list):
        text += " " + " ".join(str((e or {}).get(k) or "") for e in ev for k in ("title", "slug", "description"))
    return any(t in text for t in ("bitcoin", " btc", "btc ", "ethereum", " eth", "eth ", "solana", " sol", "sol ", "crypto", "cryptocurrency", "dogecoin", " doge", "xrp", "ripple", "cardano", " ada", "chainlink", "bnb", "avalanche", "avax", "sui", "memecoin", "meme coin"))


def topic(m):
    text = " ".join(str(m.get(k) or "") for k in ("question", "slug", "eventSlug", "description")).lower()
    if crypto_market(m): return "crypto"
    if any(x in text for x in ("nba", "nfl", "mlb", "nhl", "soccer", "football", "basketball", "baseball", "tennis", "ufc", "game", "match", "championship", "world cup")): return "sports"
    if any(x in text for x in ("trump", "democrat", "republican", "election", "president", "senate", "congress", "prime minister", "government", "strike", "war", "israel", "ukraine", "russia", "china")): return "politics"
    return "other"


def market_url(m):
    ev = m.get("events") or []
    event_slug = str((ev[0] or {}).get("slug") or "") if isinstance(ev, list) and ev else ""
    slug = event_slug or str(m.get("eventSlug") or m.get("slug") or "")
    return f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com/"


def model(m):
    p = yes_prob(m); v = volume(m); l = liquidity(m)
    vq = min(1, math.log10(max(v, 10)) / 7)
    lq = min(1, math.log10(max(l, 10)) / 6) if l else vq * .75
    q = max(.2, min(1, .65 * vq + .35 * lq))
    ext = (-7*q if p >= 80 else 7*q if p <= 20 else -3.5*q if p >= 68 else 3.5*q if p <= 32 else 0)
    center = abs(p - 50) / 50
    conv = (5.2 + 2.8*q) * (.55 + .45*center)
    est = max(5, min(95, p + ext + (1 if p >= 50 else -1) * conv))
    pick = "YES" if est >= 50 else "NO"
    conf = round(est if pick == "YES" else 100-est)
    side = p if pick == "YES" else 100-p
    edge = conf - side
    reason = f"Rules-v2: market {p:.1f}% YES; volume ${v:,.0f}; liquidity ${l:,.0f}; quality {q:.2f}; model {est:.1f}% YES."
    return pick, conf, edge, reason, p, v, l


def main():
    state = json.loads(DATA.read_text(encoding="utf-8"))
    if state.get(MARKER):
        raise SystemExit("Already completed: this one-time script will not add another 3 predictions.")

    preds = state.setdefault("predictions", [])
    existing = {str(p.get("id")) for p in preds if p.get("id") is not None}
    retired = {str(x) for x in state.get("retired_market_ids", [])}
    open_count = sum(str(p.get("status", "")).lower() == "open" for p in preds if not p.get("seeded_demo", False))
    if open_count + COUNT > 100:
        raise SystemExit(f"Refusing to exceed 100 live calls: currently {open_count} open.")

    active, seen = [], set()
    for offset in range(0, 2000, 100):
        url = GAMMA + "?" + urllib.parse.urlencode({"active": "true", "closed": "false", "limit": "100", "offset": offset})
        page = get_json(url)
        if not page: break
        for m in page:
            mid = str(m.get("id") or "")
            if mid and mid not in seen:
                seen.add(mid); active.append(m)
        if len(page) < 100: break

    candidates = []
    for m in active:
        mid = str(m.get("id") or "")
        if not mid or mid in existing or mid in retired: continue
        h = hours_left(m)
        if h is None or h <= 0 or h > 24: continue
        v, l = volume(m), liquidity(m)
        if not (v >= MIN_VOLUME or (v == 0 and l >= MIN_VOLUME)): continue
        p = yes_prob(m)
        if p <= 3 or p >= 97: continue
        pick, conf, edge, reason, yesp, v, l = model(m)
        if edge < 0: continue
        quality = min(2, math.log10(max(v, 1))/4) + min(1.5, math.log10(max(l, 1))/4 if l else 0)
        score = edge + 30 + (2 if 10 <= p <= 90 else -2) + quality + (6 if crypto_market(m) else 0)
        candidates.append((score, v, h, m, pick, conf, edge, reason, yesp, l, topic(m)))

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    chosen = []
    used_topics = set()
    # Prefer topic variety first.
    for c in candidates:
        if c[-1] not in used_topics:
            chosen.append(c); used_topics.add(c[-1])
            if len(chosen) == COUNT: break
    if len(chosen) < COUNT:
        chosen_ids = {str(c[3].get("id")) for c in chosen}
        for c in candidates:
            if str(c[3].get("id")) in chosen_ids: continue
            chosen.append(c)
            if len(chosen) == COUNT: break

    if len(chosen) < COUNT:
        raise SystemExit(f"Found only {len(chosen)} qualifying <=24h markets; nothing was changed.")

    stamp = now()
    for score, v, h, m, pick, conf, edge, reason, yesp, l, cat in chosen:
        e = parse_end(m)
        preds.append({
            "id": str(m["id"]), "slug": m.get("slug"), "question": m.get("question", "Untitled market"),
            "pick": pick, "confidence": conf, "market_probability_at_pick": round(yesp, 2),
            "market_probability_current": round(yesp, 2), "edge_at_pick": round(edge, 2),
            "selection_score": round(score, 2), "hours_to_resolution_at_pick": round(h, 1),
            "market_end_date": e.isoformat().replace("+00:00", "Z"), "volume": v, "liquidity": l,
            "locked_at": stamp, "updated_at": stamp, "status": "open", "result": None, "resolved_at": None,
            "market_url": market_url(m), "reason": reason, "model_version": "rules-v2-one-time-quick",
            "category": cat, "seeded_demo": False
        })

    state[MARKER] = {"completed_at": stamp, "count": COUNT, "market_ids": [str(c[3]["id"]) for c in chosen]}
    state["updated_at"] = stamp
    DATA.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("Added exactly 3 one-time <=24h CERTAINU predictions:")
    for c in chosen:
        print(f" - [{c[-1]}] {c[3].get('question')} ({c[2]:.1f}h left)")
    print("Done. This script is now locked against running again on this predictions file.")


if __name__ == "__main__":
    main()
