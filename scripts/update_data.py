#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

WORLDS = [1177, 1178, 1179, 1180]
RANKINGS = [
    (2, "guild", "GuildData"),
    (1, "player", "PlayerData"),
]
OUT = Path("data")
OUT.mkdir(exist_ok=True)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
)

summary = {"updated_at_utc": None, "worlds": {}}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(locale="ja-JP", user_agent=USER_AGENT)
    page = context.new_page()

    bootstrap_url = "https://tamamo.dev/Rankings?world=1177&ranking=2&display=3"
    print("BOOTSTRAP", bootstrap_url)
    with page.expect_response(
        lambda r: "getRanking/1177?ranking=2&display=3" in r.url,
        timeout=90000,
    ) as info:
        page.goto(bootstrap_url, wait_until="domcontentloaded", timeout=90000)
    bootstrap = info.value
    print("BOOTSTRAP RESPONSE", bootstrap.status, bootstrap.url)
    if bootstrap.status != 200:
        raise RuntimeError(f"Bootstrap failed: HTTP {bootstrap.status}")

    raw_headers = bootstrap.request.all_headers()
    blocked = {"host", "content-length"}
    headers = {
        k: v for k, v in raw_headers.items()
        if not k.startswith(":") and k.lower() not in blocked
    }
    print("REUSED HEADER NAMES", sorted(headers.keys()))

    for world in WORLDS:
        wkey = str(world)
        summary["worlds"][wkey] = {}
        for ranking, kind, data_key in RANKINGS:
            api_url = f"https://api.tamamo.dev/getRanking/{world}?ranking={ranking}&display=3"
            print("FETCH", api_url)
            resp = context.request.get(api_url, headers=headers, timeout=90000)
            print("RESPONSE", resp.status, api_url)
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}: {api_url}")

            payload = resp.json()
            data = payload.get("data") or {}
            ids = data.get("WorldID") or []
            rows = data.get(data_key)
            if not ids or int(ids[0]) != world or not isinstance(rows, list):
                raise RuntimeError(
                    f"Invalid response world={world} ranking={ranking} key={data_key}"
                )

            path = OUT / f"{kind}_{world}.json"
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            summary["worlds"][wkey][f"{kind}s"] = len(rows)
            print(f"SAVED {kind} world={world} rows={len(rows)}")

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
