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

def wait_until(page, pred, timeout_ms=20000):
    elapsed = 0
    while elapsed < timeout_ms:
        if pred():
            return True
        page.wait_for_timeout(500)
        elapsed += 500
    return False

summary = {"updated_at_utc": None, "worlds": {}}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for world in WORLDS:
        print(f"=== WORLD {world} ===")
        summary["worlds"][str(world)] = {}
        context = browser.new_context(locale="ja-JP", user_agent=USER_AGENT)
        page = context.new_page()
        captured = {}
        seen_urls = []

        def on_response(response, world=world):
            if f"getRanking/{world}" not in response.url:
                return
            seen_urls.append(response.url)
            print("FOUND", response.status, response.url)
            if response.status != 200 or "display=3" not in response.url:
                return
            try:
                payload = response.json()
                data = payload.get("data") or {}
                ids = data.get("WorldID") or []
                if not ids or int(ids[0]) != world:
                    return

                if "ranking=2" in response.url and isinstance(data.get("GuildData"), list):
                    rows = data["GuildData"]
                    (OUT / f"guild_{world}.json").write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    captured[2] = len(rows)
                    print(f"SAVED guild world={world} rows={len(rows)}")

                if "ranking=1" in response.url and isinstance(data.get("PlayerData"), list):
                    rows = data["PlayerData"]
                    (OUT / f"player_{world}.json").write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    captured[1] = len(rows)
                    print(f"SAVED player world={world} rows={len(rows)}")
            except Exception as exc:
                print("RESPONSE ERROR", repr(exc))

        page.on("response", on_response)
        guild_url = f"https://tamamo.dev/Rankings?world={world}&ranking=2&display=3"
        print("OPEN", guild_url)
        page.goto(guild_url, wait_until="domcontentloaded", timeout=90000)

        if not wait_until(page, lambda: 2 in captured, 25000):
            raise RuntimeError(f"Guild ranking not captured for {world}; seen={seen_urls}")

        summary["worlds"][str(world)]["guilds"] = captured[2]

        clickable = page.locator("button, a, [role=button]")
        try:
            texts = clickable.all_inner_texts()
            print("CLICKABLE TEXTS", [t.strip() for t in texts if t.strip()][:120])
        except Exception as exc:
            print("CLICKABLE TEXTS ERROR", repr(exc))

        clicked = False
        for label in ["プレイヤー", "個人"]:
            candidates = [
                page.get_by_role("button", name=label, exact=True),
                page.get_by_role("link", name=label, exact=True),
                page.get_by_text(label, exact=True),
            ]
            for loc in candidates:
                try:
                    if loc.count() > 0:
                        loc.first.click(timeout=8000)
                        print("CLICKED", label)
                        clicked = True
                        break
                except Exception as exc:
                    print("CLICK ERROR", label, repr(exc))
            if clicked:
                break

        if not clicked:
            raise RuntimeError(f"Player tab/button not found for {world}")

        if not wait_until(page, lambda: 1 in captured, 25000):
            print("PLAYER CAPTURE FAILED; current URL", page.url)
            print("SEEN getRanking URLS", seen_urls)
            raise RuntimeError(f"Player ranking not captured for {world}")

        summary["worlds"][str(world)]["players"] = captured[1]
        context.close()

    browser.close()

summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
(OUT / "status.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
