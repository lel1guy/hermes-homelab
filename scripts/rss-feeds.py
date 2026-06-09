#!/usr/bin/env python3
"""rss-feeds.py — Poll RSS feeds and output new items.

State file: ~/.hermes/rss_state.json
Config: vault/_hermes/Scripts/feeds.json
Silent when nothing new (empty stdout = no delivery).
"""

import json
import os
import time
from pathlib import Path

import feedparser

CONFIG = Path(os.path.expanduser("~/vault/_hermes/Scripts/feeds.json"))
STATE = Path(os.path.expanduser("~/.hermes/rss_state.json"))
LIMIT_PER_FEED = 3  # max items per feed per poll


def load_config():
    with open(CONFIG) as f:
        return json.load(f)


def load_state():
    if STATE.exists():
        with open(STATE) as f:
            return json.load(f)
    return {"seen": {}, "last_run": 0}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f)


def poll_feed(feed_info):
    """Fetch a feed and return unpublished items."""
    name = feed_info["name"]
    url = feed_info["url"]
    cat = feed_info.get("category", "misc")
    state = load_state()
    seen = state.get("seen", {})

    try:
        feed = feedparser.parse(url)
    except Exception as e:
        return [], f"  ⚠️ **{name}** — fetch error: {e}"

    if feed.bozo and not feed.entries:
        return [], f"  ⚠️ **{name}** — parse error: {feed.bozo_exception}"

    new_items = []
    for entry in feed.entries[:LIMIT_PER_FEED]:
        guid = entry.get("id") or entry.get("link", "")
        if guid in seen:
            continue
        seen[guid] = True
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        published = entry.get("published", "")
        new_items.append({
            "title": title,
            "link": link,
            "published": published,
            "category": cat,
            "feed": name,
        })

    if new_items:
        state["seen"] = seen
        save_state(state)

    return new_items, None


def format_items(items):
    """Group items by category and format as markdown."""
    if not items:
        return None

    # Group
    grouped = {}
    for item in items:
        cat = item["category"]
        grouped.setdefault(cat, []).append(item)

    emoji_map = {
        "tech": "💻",
        "ai": "🤖",
        "gaming": "🎮",
        "cybersecurity": "🔐",
        "devtools": "🛠️",
        "homelab": "🏠",
        "misc": "📌",
    }

    lines = ["## 📡 Fresh from the feeds\n"]
    for cat, cat_items in grouped.items():
        emoji = emoji_map.get(cat, "📌")
        cat_name = cat.capitalize()
        lines.append(f"**{emoji} {cat_name}**")
        for item in cat_items:
            title = item["title"].replace("\\", "").replace("`", "'").replace("*", "·")
            lines.append(f"  • [{title}]({item['link']})")
            if item["published"]:
                lines[-1] += f" — {item['published']}"
        lines.append("")

    lines.append("---")
    return "\n".join(lines)


def main():
    config = load_config()
    all_new = []
    errors = []

    for feed in config["feeds"]:
        new_items, err = poll_feed(feed)
        if err:
            errors.append(err)
        all_new.extend(new_items)

    output = format_items(all_new)
    if output:
        print(output)

    if errors:
        # Always output errors so we don't miss them silently
        print("\n".join(errors))


if __name__ == "__main__":
    main()
