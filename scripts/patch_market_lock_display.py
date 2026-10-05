#!/usr/bin/env python3
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "index.html"
s = P.read_text(encoding="utf-8")

# Add the at-pick probability to the renderer calculations.
old = "  const yesNow=Math.max(0,Math.min(100,Number(p.market_probability_current ?? p.market_probability_at_pick ?? 0)));\n  const noNow=100-yesNow;"
new = "  const yesNow=Math.max(0,Math.min(100,Number(p.market_probability_current ?? p.market_probability_at_pick ?? 0)));\n  const noNow=100-yesNow;\n  const yesLock=Math.max(0,Math.min(100,Number(p.market_probability_at_pick ?? yesNow)));\n  const noLock=100-yesLock;"
if old in s:
    s = s.replace(old, new, 1)
elif "const yesLock=" not in s:
    raise SystemExit("ERROR: prediction probability calculation anchor not found")

# Replace the old single ambiguous marker with clearly labeled NOW + AT PICK markers
# and an explicit lock-vs-current summary below the meter.
old_meter = '''      <div class="yn-market-meter" aria-label="Polymarket probability">
        <div class="yn-market-fill" style="width:${yesNow}%"></div>
        <span class="yn-market-marker" style="left:${yesNow}%"></span>
      </div>
      <div class="yn-market-values">
        <span><b>${Math.round(yesNow)}%</b> YES</span>
        <span><b>${Math.round(noNow)}%</b> NO</span>
      </div>'''
new_meter = '''      <div class="yn-market-meter yn-market-meter-enhanced" aria-label="Polymarket probability; ${Math.round(yesLock)}% YES at pick, ${Math.round(yesNow)}% YES now">
        <div class="yn-market-fill" style="width:${yesNow}%"></div>
        <span class="yn-now-marker" style="left:${yesNow}%"><em>${Math.round(yesNow)}% NOW</em></span>
        <span class="yn-lock-marker" style="left:${yesLock}%"><em>🔒 ${Math.round(yesLock)}% AT PICK</em></span>
      </div>
      <div class="yn-market-values">
        <span><b>${Math.round(yesNow)}%</b> YES</span>
        <span><b>${Math.round(noNow)}%</b> NO</span>
      </div>
      <div class="yn-market-lock-summary">
        <span>MARKET AT LOCK: <b>${Math.round(yesLock)}% YES</b> / <b>${Math.round(noLock)}% NO</b></span>
        <i></i>
        <span>MARKET NOW: <b>${Math.round(yesNow)}% YES</b> / <b>${Math.round(noNow)}% NO</b></span>
      </div>'''
if old_meter in s:
    s = s.replace(old_meter, new_meter, 1)
elif "yn-market-lock-summary" not in s:
    raise SystemExit("ERROR: Polymarket meter anchor not found")

style = '''<style id="certainu-market-lock-enhancements">
#markets .yn-market-meter-enhanced{margin-top:30px;overflow:visible!important;position:relative}
#markets .yn-market-meter-enhanced .yn-market-fill{overflow:hidden}
#markets .yn-now-marker,#markets .yn-lock-marker{position:absolute;top:50%;transform:translate(-50%,-50%);z-index:3}
#markets .yn-now-marker{width:12px;height:12px;border:3px solid #fff;border-radius:50%;background:#22c55e;box-shadow:0 0 0 2px rgba(15,49,151,.8)}
#markets .yn-lock-marker{width:5px;height:27px;background:#fff;border-radius:4px;box-shadow:0 0 0 2px rgba(15,49,151,.82),0 0 12px rgba(255,255,255,.55)}
#markets .yn-now-marker em,#markets .yn-lock-marker em{position:absolute;bottom:22px;left:50%;transform:translateX(-50%);white-space:nowrap;font-style:normal;font-size:9px;font-weight:950;letter-spacing:.04em;padding:5px 8px;border-radius:999px;background:#0b2f91;color:#fff;border:1px solid rgba(255,255,255,.28);box-shadow:0 4px 12px rgba(4,18,76,.25)}
#markets .yn-now-marker em{color:#7df29e}
#markets .yn-lock-marker em{bottom:25px;background:#1747df;border-color:rgba(255,255,255,.65)}
#markets .yn-market-lock-summary{display:flex;align-items:center;justify-content:center;gap:12px;margin:9px 22px 15px;padding:8px 12px;border-radius:10px;background:rgba(5,28,104,.38);font-size:9px;font-weight:850;letter-spacing:.025em;color:rgba(255,255,255,.76)}
#markets .yn-market-lock-summary b{color:#fff;font-weight:950}
#markets .yn-market-lock-summary i{width:1px;height:13px;background:rgba(255,255,255,.28)}
#markets .yn-choice-title small{font-size:12px!important;font-weight:900!important;opacity:.82!important;letter-spacing:.015em}
@media(max-width:700px){#markets .yn-now-marker em,#markets .yn-lock-marker em{font-size:7px;padding:4px 6px}#markets .yn-market-lock-summary{font-size:7px;gap:7px;margin-left:12px;margin-right:12px}#markets .yn-choice-title small{font-size:10px!important}}
</style>'''

start = s.find('<style id="certainu-market-lock-enhancements">')
if start != -1:
    end = s.find('</style>', start)
    if end == -1:
        raise SystemExit("ERROR: malformed existing market lock style")
    s = s[:start] + style + s[end+8:]
else:
    if '</head>' not in s:
        raise SystemExit("ERROR: </head> not found")
    s = s.replace('</head>', style + '\n</head>', 1)

P.write_text(s, encoding="utf-8")
print("CERTAINU market display patched: AT PICK marker + NOW marker + larger confidence text")
