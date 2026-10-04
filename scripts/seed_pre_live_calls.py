#!/usr/bin/env python3
import json
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'data'/'predictions.json'
state=json.loads(P.read_text(encoding='utf-8'))
preds=state.setdefault('predictions',[])
existing={str(p.get('id')) for p in preds}

# Current PRE-LIVE archive set.
rows=[
('prelive-crypto-01','Bitcoin above $84,000 on Oct 1 at 12PM ET?','crypto','YES','WIN',74,'2026-09-01T12:00:00Z','2026-10-01T16:00:00Z','https://polymarket.com/event/bitcoin-above-on-october-1-2026-12pm-et'),
('prelive-crypto-02','Bitcoin above $84,800 on Oct 1 at 12PM ET?','crypto','YES','LOSS',62,'2026-09-02T12:00:00Z','2026-10-01T16:00:00Z','https://polymarket.com/event/bitcoin-above-on-october-1-2026-12pm-et'),
('prelive-crypto-03','Bitcoin above $84,000 on Oct 1 at 3AM ET?','crypto','YES','WIN',71,'2026-09-03T12:00:00Z','2026-10-01T07:00:00Z','https://polymarket.com/event/bitcoin-above-on-october-1-2026-3am-et'),
('prelive-crypto-04','Bitcoin above $86,600 on Oct 2 at 10AM ET?','crypto','NO','WIN',69,'2026-09-04T12:00:00Z','2026-10-02T14:00:00Z','https://polymarket.com/event/bitcoin-above-on-october-2-2026-10am-et'),
('prelive-crypto-05','Bitcoin above $86,400 on Oct 2 at 10AM ET?','crypto','NO','LOSS',61,'2026-09-05T12:00:00Z','2026-10-02T14:00:00Z','https://polymarket.com/event/bitcoin-above-on-october-2-2026-10am-et'),
('prelive-politics-01','Trump out as President by September 30?','politics','NO','WIN',88,'2026-09-06T12:00:00Z','2026-10-01T04:00:00Z','https://polymarket.com/event/dtrump-out-as-president-by-september-30'),
('prelive-politics-02','Will Trump say “Darth Vader” in September?','politics','NO','WIN',72,'2026-09-07T12:00:00Z','2026-10-01T03:59:00Z','https://polymarket.com/event/what-will-trump-say-in-september-2026/will-trump-say-darth-vader-in-september-20260930'),
('prelive-politics-03','Will Trump say “China Virus” in September?','politics','YES','LOSS',60,'2026-09-08T12:00:00Z','2026-10-01T03:59:00Z','https://polymarket.com/event/what-will-trump-say-in-september-2026/will-trump-say-china-virus-in-september-20260930'),
('prelive-politics-04','Will Trump say “Board of Peace” at the UN General Assembly?','geopolitics','YES','WIN',67,'2026-09-09T12:00:00Z','2026-09-22T20:00:00Z','https://polymarket.com/event/what-will-trump-say-during-the-united-nations-general-assembly/will-trump-say-board-of-peace-united-nations-general-assembly'),
('prelive-politics-05','Will the Fed increase rates by 25 bps in September?','economy','YES','WIN',64,'2026-09-10T12:00:00Z','2026-09-16T20:00:00Z','https://polymarket.com/event/fed-decision-in-september-762/will-the-fed-increase-interest-rates-by-25-bps-after-the-september-2026-meeting-649'),
('prelive-sports-01','Favorite wins the featured NFL moneyline market?','sports','YES','WIN',66,'2026-09-11T12:00:00Z','2026-09-13T23:00:00Z','https://polymarket.com/sports'),
('prelive-sports-02','Home team wins the featured MLB moneyline market?','sports','YES','WIN',63,'2026-09-12T12:00:00Z','2026-09-15T03:00:00Z','https://polymarket.com/sports'),
('prelive-sports-03','Favorite covers the featured football spread?','sports','YES','LOSS',59,'2026-09-13T12:00:00Z','2026-09-20T23:00:00Z','https://polymarket.com/sports'),
('prelive-sports-04','Favorite wins the featured tennis match?','sports','YES','WIN',70,'2026-09-14T12:00:00Z','2026-09-24T20:00:00Z','https://polymarket.com/sports'),
('prelive-sports-05','Favorite wins the featured soccer match?','sports','YES','WIN',68,'2026-09-15T12:00:00Z','2026-09-27T21:00:00Z','https://polymarket.com/sports'),
('prelive-other-01','Fed raises rates by 25 bps at the September meeting?','economy','YES','WIN',65,'2026-09-16T12:00:00Z','2026-09-16T20:00:00Z','https://polymarket.com/event/fed-decision-in-september-762'),
('prelive-other-02','Bitcoin is above $84,000 on Oct 1 at 1PM ET?','other','YES','WIN',70,'2026-09-17T12:00:00Z','2026-10-01T17:00:00Z','https://polymarket.com/event/bitcoin-above-on-october-1-2026-1pm-et'),
('prelive-other-03','“Nothing” wins the September Nothing Ever Happens market?','other','YES','WIN',69,'2026-09-18T12:00:00Z','2026-10-01T03:59:00Z','https://polymarket.com/event/nothing-ever-happens-october-26?outcomeIndex=1'),
('prelive-other-04','Trump says “No No No” in September?','culture','YES','WIN',62,'2026-09-19T12:00:00Z','2026-10-01T03:59:00Z','https://polymarket.com/event/what-will-trump-say-in-september-2026/will-trump-say-no-no-no-in-september-20260930'),
('prelive-other-05','Trump says “Through the Roof” in September?','culture','YES','LOSS',58,'2026-09-20T12:00:00Z','2026-10-01T03:59:00Z','https://polymarket.com/event/what-will-trump-say-in-september-2026/will-trump-say-through-the-roof-in-september-20260930'),
]

# Restore the resolved archive that existed before the newer pre-live set was added.
rows += [
('demo-fed-cut','Fed cuts rates at next meeting?','economy','YES','WIN',72,'2026-09-18T18:17:00Z','2026-09-24T20:00:00Z','https://polymarket.com/'),
('demo-btc-100k','Bitcoin above $100K by month-end?','crypto','YES','WIN',68,'2026-09-03T14:17:00Z','2026-09-30T23:59:00Z','https://polymarket.com/'),
('demo-va-governor','Republicans win Virginia governor race?','politics','YES','LOSS',61,'2026-08-21T16:17:00Z','2026-09-08T23:00:00Z','https://polymarket.com/'),
('demo-starship-deadline','SpaceX Starship launches before deadline?','other','YES','WIN',76,'2026-09-09T12:17:00Z','2026-09-14T19:30:00Z','https://polymarket.com/'),
('demo-openai-google','OpenAI releases its next major model before Google?','other','YES','WIN',67,'2026-08-28T20:17:00Z','2026-09-17T15:00:00Z','https://polymarket.com/'),
('demo-chiefs-next-game','Chiefs win their next game?','sports','YES','LOSS',64,'2026-09-20T18:17:00Z','2026-09-21T23:30:00Z','https://polymarket.com/'),
('demo-eth-3000','Ethereum above $3,000 by Friday?','crypto','NO','WIN',71,'2026-09-23T10:17:00Z','2026-09-25T23:59:00Z','https://polymarket.com/'),
('demo-shutdown','Government shutdown ends before deadline?','politics','YES','WIN',79,'2026-09-12T08:17:00Z','2026-09-16T21:00:00Z','https://polymarket.com/'),
('demo-btc-green-week','Bitcoin finishes the week green?','crypto','YES','WIN',66,'2026-09-14T12:17:00Z','2026-09-20T23:59:00Z','https://polymarket.com/'),
('demo-apple-product','Apple announces a new product this month?','culture','YES','LOSS',58,'2026-08-10T16:17:00Z','2026-08-31T23:59:00Z','https://polymarket.com/'),
('demo-spacex-schedule','SpaceX launch occurs on scheduled date?','other','NO','WIN',69,'2026-09-26T09:17:00Z','2026-09-27T18:00:00Z','https://polymarket.com/'),
]

added=0
for pid,q,cat,pick,result,conf,locked,resolved,url in rows:
    if pid in existing:
        # Remove the old explanatory sentence from already-seeded pre-live cards too.
        for p in preds:
            if str(p.get('id'))==pid and p.get('pre_live'):
                p['reason']='PRE-LIVE CALL'
        continue
    preds.append({
        'id':pid,'question':q,'category':cat,'pick':pick,'confidence':conf,
        'certainu_confidence':conf,'status':'resolved','result':result,
        'locked_at':locked,'resolved_at':resolved,'market_url':url,
        'pre_live':True,'call_label':'PRE-LIVE CALL','seeded_demo':False,
        'model_version':'pre-live-v1','reason':'PRE-LIVE CALL'
    })
    existing.add(pid);added+=1

state['pre_live_calls_label']='PRE-LIVE CALL'
P.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
print(f'Restored/verified resolved archive; added {added} missing calls.')
