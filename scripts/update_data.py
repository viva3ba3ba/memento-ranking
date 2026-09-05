#!/usr/bin/env python3
import json
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


def wait_until(page, pred, timeout_ms=45000):
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


def capture_world(browser, world):
    context = browser.new_context(locale="ja-JP", user_agent=USER_AGENT)
    page = context.new_page()
    payloads = {}
    seen = []

    def relevant(url):
        return f"getRanking/{world}" in url

    def on_request(request):
        if relevant(request.url):
            print("REQUEST", request.method, request.url)

    def on_failed(request):
        if relevant(request.url):
            print("REQUEST FAILED", request.url, request.failure)

    def on_response(response):
        if not relevant(response.url):
            return
        seen.append(response.url)
        print("FOUND", response.status, response.url)
        if response.status != 200 or "display=3" not in response.url:
            return
        try:
            if "ranking=2" in response.url:
                payloads["guild"] = response.json()
            elif "ranking=1" in response.url:
                payloads["player"] = response.json()
        except Exception as exc:
            print("RESPONSE ERROR", repr(exc))

    page.on("request", on_request)
    page.on("requestfailed", on_failed)
    page.on("response", on_response)

    url = f"https://tamamo.dev/Rankings?world={world}&ranking=2&display=3"
    print("OPEN", url)
    page.goto(url, wait_until="domcontentloaded", timeout=90000)

    if not wait_until(page, lambda: "guild" in payloads, 30000):
        context.close()
        raise RuntimeError(f"guild ranking not captured for {world}; seen={seen}")

    guild_count = save_payload("guild", world, payloads["guild"])

    print("SWITCH TO PLAYER")
    page.get_by_text("プレイヤー", exact=True).first.click(timeout=10000)
    print("PLAYER URL", page.url)

    if not wait_until(page, lambda: "player" in payloads, 45000):
        try:
            disabled = page.locator("#search-exec").is_disabled(timeout=3000)
            print("SEARCH DISABLED", disabled)
        except Exception:
            pass
        print("CURRENT URL", page.url)
        context.close()
        raise RuntimeError(f"player ranking not captured for {world}; seen={seen}")

    player_count = save_payload("player", world, payloads["player"])
    context.close()
    return guild_count, player_count


summary = {"updated_at_utc": None, "worlds": {}}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for world in WORLDS:
        print(f"=== WORLD {world} ===")
        guild_count, player_count = capture_world(browser, world)
        summary["worlds"][str(world)] = {
            "guilds": guild_count,
            "players": player_count,
        }

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
