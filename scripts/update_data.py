#!/usr/bin/env python3
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

WORLD = 1177
URL = f"https://tamamo.dev/Rankings?world={WORLD}&ranking=2&display=3"
out = Path("data")
out.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="ja-JP",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    found = []

    def on_response(response):
        if "getRanking" not in response.url:
            return
        print("FOUND", response.status, response.url)
        if f"getRanking/{WORLD}" not in response.url or "ranking=2" not in response.url:
            return
        try:
            payload = response.json()
            data = payload.get("data") or {}
            ids = data.get("WorldID") or []
            guilds = data.get("GuildData")
            if ids and int(ids[0]) == WORLD and isinstance(guilds, list):
                (out / f"guild_{WORLD}.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                found.append(len(guilds))
                print(f"SAVED W177 guilds={len(guilds)}")
        except Exception as exc:
            print("RESPONSE ERROR", repr(exc))

    page.on("response", on_response)
    print("OPEN", URL)
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(15000)
    print("TITLE", page.title())
    print("FINAL URL", page.url)
    browser.close()

if not found:
    raise RuntimeError("W177 getRanking response was not captured")
print("SUCCESS", found[-1])
