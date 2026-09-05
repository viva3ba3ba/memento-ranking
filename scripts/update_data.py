#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

WORLDS = [1177, 1178, 1179, 1180]
OUT = Path("data")
OUT.mkdir(exist_ok=True)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
)


def wait_until(page, pred, timeout_ms=25000):
    elapsed = 0
    while elapsed < timeout_ms:
        if pred():
            return True
        page.wait_for_timeout(500)
        elapsed += 500
    return False


def save_payload(kind, world, payload):
    data = payload.get("data") or {}
    ids = data.get("WorldID") or []
    if not ids or int(ids[0]) != world:
        raise RuntimeError(f"Unexpected WorldID for {kind} {world}: {ids[:3]}")

    key = "GuildData" if kind == "guild" else "PlayerData"
    rows = data.get(key)
    if not isinstance(rows, list):
        raise RuntimeError(f"Missing {key} for {world}")

    (OUT / f"{kind}_{world}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"SAVED {kind} world={world} rows={len(rows)}")
    return len(rows)


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "*/*",
            "User-Agent": USER_AGENT,
            "Referer": "https://tamamo.dev/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


summary = {"updated_at_utc": None, "worlds": {}}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for world in WORLDS:
        print(f"=== WORLD {world} ===")
        summary["worlds"][str(world)] = {}
        context = browser.new_context(locale="ja-JP", user_agent=USER_AGENT)
        page = context.new_page()
        guild_payload = {}
        seen_urls = []

        def on_response(response, world=world):
            if f"getRanking/{world}" not in response.url:
                return
            seen_urls.append(response.url)
            print("FOUND", response.status, response.url)
            if response.status != 200 or "display=3" not in response.url:
                return
            if "ranking=2" not in response.url:
                return
            try:
                guild_payload["value"] = response.json()
            except Exception as exc:
                print("GUILD RESPONSE ERROR", repr(exc))

        page.on("response", on_response)

        guild_url = f"https://tamamo.dev/Rankings?world={world}&ranking=2&display=3"
        print("OPEN", guild_url)
        page.goto(guild_url, wait_until="domcontentloaded", timeout=90000)
        if not wait_until(page, lambda: "value" in guild_payload):
            raise RuntimeError(f"Guild ranking not captured for {world}; seen={seen_urls}")

        summary["worlds"][str(world)]["guilds"] = save_payload(
            "guild", world, guild_payload["value"]
        )

        player_api = f"https://api.tamamo.dev/getRanking/{world}?ranking=1&display=3"
        print("FETCH PLAYER API", player_api)
        player_payload = fetch_json(player_api)
        summary["worlds"][str(world)]["players"] = save_payload(
            "player", world, player_payload
        )
        context.close()

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
