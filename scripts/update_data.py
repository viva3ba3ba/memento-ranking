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

summary = {
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    "worlds": {},
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="ja-JP",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        ),
    )

    for world in WORLDS:
        wkey = str(world)
        summary["worlds"][wkey] = {}

        for ranking, kind, data_key in RANKINGS:
            url = f"https://tamamo.dev/Rankings?world={world}&ranking={ranking}&display=3"
            print("OPEN", url)
            page = context.new_page()

            with page.expect_response(
                lambda r, world=world, ranking=ranking: (
                    f"getRanking/{world}" in r.url
                    and f"ranking={ranking}" in r.url
                    and "display=3" in r.url
                ),
                timeout=90000,
            ) as resp_info:
                page.goto(url, wait_until="domcontentloaded", timeout=90000)

            response = resp_info.value
            print("FOUND", response.status, response.url)
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}: {response.url}")

            payload = response.json()
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
            page.close()

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
