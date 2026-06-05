#!/usr/bin/env python3
"""rss-feeds.py — Fetch RSS feeds and post new items to Discord.

Runs every 4h via cron (no_agent). Tracks seen GUIDs in state file.
Only posts items not seen before. Silent when nothing new.
"""

import json
import os
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(os.path.expanduser("~/.hermes/rss_state.json"))
FEEDS_FILE = Path(os.path.expanduser("~/vault/_hermes/Scripts/feeds.json"))

USER_AGENT = "Hermes-RSS/1.0"


def fetch_feed(url: str) -> str | None:
    """Fetch an RSS/Atom feed."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️ Failed: {e}")
        return None


def parse_entries(xml_data: str) -> list[dict]:
    """Parse RSS 2.0, Atom, or RDF feed, returns entries with guid, title, link."""
    root = ET.fromstring(xml_data)
    entries = []

    # RSS 2.0
    for item in root.iter("item"):
        guid = item.findtext("guid") or item.findtext("link") or ""
        entries.append({
            "guid": guid.strip(),
            "title": (item.findtext("title") or "(no title)").strip(),
            "link": (item.findtext("link") or "").strip(),
        })

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        guid = entry.findtext("atom:id", "", ns) or ""
        title_el = entry.find("atom:title", ns)
        link_el = entry.find("atom:link", ns)
        entries.append({
            "guid": guid.strip(),
            "title": (title_el.text or "(no title)").strip() if title_el is not None else "(no title)",
            "link": (link_el.attrib.get("href", "") if link_el is not None else "").strip(),
        })

    return entries


def main():
    FEEDS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not FEEDS_FILE.exists():
        print("No feeds.json found — skipping")
        return

    feeds = json.loads(FEEDS_FILE.read_text())
    if not isinstance(feeds, dict):
        feeds = {"feeds": feeds}

    state = {"seen": {}}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    seen = state.get("seen", {})
    new_items = []

    for name, url in feeds.get("feeds", {}).items():
        print(f"📡 {name}")
        xml_data = fetch_feed(url)
        if not xml_data:
            continue
        try:
            entries = parse_entries(xml_data)
        except ET.ParseError as e:
            print(f"  ⚠️ Parse error: {e}")
            continue

        count = 0
        for entry in entries:
            if entry["guid"] and entry["guid"] not in seen:
                seen[entry["guid"]] = datetime.now().isoformat()
                new_items.append(entry)
                count += 1

        if count == 0:
            print(f"  No new items")

    # Save state
    state["seen"] = seen
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

    # Output new items
    if new_items:
        print(f"\n**📰 New RSS Items ({len(new_items)}):**")
        for item in new_items[:15]:
            title = item["title"]
            link = item.get("link", "")
            if link:
                print(f"- [{title}]({link})")
            else:
                print(f"- {title}")
        if len(new_items) > 15:
            print(f"  _…and {len(new_items) - 15} more_")


if __name__ == "__main__":
    main()
