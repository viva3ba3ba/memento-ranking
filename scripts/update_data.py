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


def wait_until(page, pred, timeout_ms=30000):
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


def capture_ranking(browser, world, ranking, kind):
    context = browser.new_context(locale="ja-JP", user_agent=USER_AGENT)
    page = context.new_page()
    captured = {}
    seen = []

    def on_response(response):
        if f"getRanking/{world}" not in response.url:
            return
        seen.append(response.url)
        print("FOUND", response.status, response.url)
        if response.status != 200:
            return
        if f"ranking={ranking}" not in response.url or "display=3" not in response.url:
            return
        try:
            captured["payload"] = response.json()
        except Exception as exc:
            print("RESPONSE ERROR", repr(exc))

    page.on("response", on_response)
    url = f"https://tamamo.dev/Rankings?world={world}&ranking={ranking}&display=3"
    print("OPEN", url)
    page.goto(url, wait_until="domcontentloaded", timeout=90000)

    if not wait_until(page, lambda: "payload" in captured):
        try:
            body = page.locator("body").inner_text(timeout=5000)
            print("PAGE BODY", body[:2000])
        except Exception:
            pass
        context.close()
        raise RuntimeError(f"{kind} ranking not captured for {world}; seen={seen}")

    count = save_payload(kind, world, captured["payload"])
    context.close()
    return count


summary = {"updated_at_utc": None, "worlds": {}}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for world in WORLDS:
        print(f"=== WORLD {world} ===")
        summary["worlds"][str(world)] = {}
        summary["worlds"][str(world)]["guilds"] = capture_ranking(
            browser, world, 2, "guild"
        )
        summary["worlds"][str(world)]["players"] = capture_ranking(
            browser, world, 1, "player"
        )

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
