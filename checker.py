#!/usr/bin/env python3
"""
Internship Portal Checker
--------------------------
Reads config.json (list of portals/company pages to watch), fetches each page,
figures out whether it looks OPEN or CLOSED for applications, compares against
the last known state (state.json), and sends a Telegram message only when the
status *changes*. Safe to run manually as often as you like.
"""

import json
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def get_status_keyword_mode(html, open_keywords, closed_keywords):
    """Look for open/closed keyword hints in the page's visible text."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ").lower()

    for kw in closed_keywords:
        if kw.lower() in text:
            return "CLOSED", kw
    for kw in open_keywords:
        if kw.lower() in text:
            return "OPEN", kw
    return "UNKNOWN", None


def get_status_count_listings(html):
    """
    For listing pages (e.g. Internshala search results), track the number of
    listings found. A count going from 0 -> N (or N -> 0) is treated as an
    open/close style change. Adjust the regex if the site's wording differs.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")

    match = re.search(r"([\d,]+)\s+Total Internships", text, re.IGNORECASE)
    if match:
        count = int(match.group(1).replace(",", ""))
        return ("OPEN" if count > 0 else "CLOSED"), count

    # Fallback: count of common listing-card containers
    cards = soup.select("[class*=internship_meta], [class*=job-card], [class*=individual_internship]")
    count = len(cards)
    return ("OPEN" if count > 0 else "CLOSED"), count


def send_telegram(bot_token, chat_id, message):
    if not bot_token or "PUT_YOUR" in bot_token:
        print("  [!] Telegram not configured - skipping notification. Message was:")
        print("     ", message)
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"  [!] Failed to send Telegram message: {e}")


def main():
    config = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {})

    tg = config.get("telegram", {})
    bot_token = tg.get("bot_token")
    chat_id = tg.get("chat_id")

    sources = config.get("sources", [])
    if not sources:
        print("No sources configured in config.json. Add some and re-run.")
        return

    print(f"Checking {len(sources)} source(s) at {datetime.now().isoformat(timespec='seconds')}\n")

    for src in sources:
        name = src["name"]
        url = src["url"]
        mode = src.get("mode", "keyword")

        print(f"-> {name}")
        try:
            html = fetch_page(url)
        except Exception as e:
            print(f"   Could not fetch page: {e}\n")
            continue

        if mode == "count_listings":
            status, detail = get_status_count_listings(html)
            detail_str = f"{detail} listing(s) found"
        else:
            status, detail = get_status_keyword_mode(
                html, src.get("open_keywords", []), src.get("closed_keywords", [])
            )
            detail_str = f"matched keyword: '{detail}'" if detail else "no keyword matched"

        prev = state.get(name, {}).get("status")
        print(f"   Status: {status} ({detail_str}) | Previous: {prev or 'N/A'}")

        if prev is not None and prev != status and status != "UNKNOWN":
            msg = f"🔔 {name} status changed: {prev} -> {status}\n{url}"
            print(f"   Change detected! Notifying via Telegram.")
            send_telegram(bot_token, chat_id, msg)
        elif prev is None and status != "UNKNOWN":
            print("   First check - baseline saved, no notification sent.")

        state[name] = {
            "status": status,
            "last_checked": datetime.now().isoformat(timespec="seconds"),
        }
        print()

    save_json(STATE_PATH, state)
    print("Done. State saved to state.json")


if __name__ == "__main__":
    sys.exit(main())