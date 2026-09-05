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

    for world in WORLDS:
        wkey = str(world)
        summary["worlds"][wkey] = {}

        for ranking, kind, data_key in RANKINGS:
            url = f"https://tamamo.dev/Rankings?world={world}&ranking={ranking}&display=3"
            print("OPEN", url)

            context = browser.new_context(locale="ja-JP", user_agent=USER_AGENT)
            page = context.new_page()
            captured = []

            def on_response(response, world=world, ranking=ranking, kind=kind, data_key=data_key):
                if f"getRanking/{world}" not in response.url:
                    return
                if f"ranking={ranking}" not in response.url or "display=3" not in response.url:
                    return
                print("FOUND", response.status, response.url)
                if response.status != 200:
                    return
                try:
                    payload = response.json()
                    data = payload.get("data") or {}
                    ids = data.get("WorldID") or []
                    rows = data.get(data_key)
                    if not ids or int(ids[0]) != world or not isinstance(rows, list):
                        return
                    path = OUT / f"{kind}_{world}.json"
                    path.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    captured.append(len(rows))
                    print(f"SAVED {kind} world={world} rows={len(rows)}")
                except Exception as exc:
                    print("RESPONSE ERROR", repr(exc))

            page.on("response", on_response)
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(15000)

            if not captured:
                raise RuntimeError(
                    f"No valid response captured: world={world} ranking={ranking}"
                )

            summary["worlds"][wkey][f"{kind}s"] = captured[-1]
            context.close()

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
