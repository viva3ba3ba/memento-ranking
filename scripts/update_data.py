#!/usr/bin/env python3
import json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
BASE='https://api.tamamo.dev/getRanking/{world}?ranking={ranking}&display=3'
WORLDS=(1177,1178,1179,1180)
HEADERS={'accept':'application/json, text/plain, */*','origin':'https://tamamo.dev','referer':'https://tamamo.dev/','user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/152 Safari/537.36'}
def fetch_json(url,tries=3):
    last=None
    for i in range(tries):
        try:
            with urlopen(Request(url,headers=HEADERS),timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            last=e;time.sleep(2*(i+1))
    raise last
def validate(o,w,key):
    d=o.get('data') or {};ids=d.get('WorldID') or []
    if not ids or int(ids[0])!=w or not isinstance(d.get(key),list):
        raise RuntimeError(f'invalid response for {w} {key}')
out=Path('data');out.mkdir(exist_ok=True)
summary={'updated_at_utc':datetime.now(timezone.utc).isoformat(),'worlds':{}}
for w in WORLDS:
    g=fetch_json(BASE.format(world=w,ranking=2));validate(g,w,'GuildData')
    p=fetch_json(BASE.format(world=w,ranking=1));validate(p,w,'PlayerData')
    (out/f'guild_{w}.json').write_text(json.dumps(g,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (out/f'player_{w}.json').write_text(json.dumps(p,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    summary['worlds'][str(w)]={'guilds':len(g['data']['GuildData']),'players':len(p['data']['PlayerData'])}
(out/'status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))