#!/usr/bin/env python3
"""
logbook.py — Detect vault changes since last run and format a digest.

State file: ~/.hermes/data/logbook_state.json (stores last scan mtime max)

Designed for no_agent cron delivery to #logbook.
Outputs an empty string (silent) when nothing changed.
"""

import json
import os
import time
from pathlib import Path

VAULT = Path(os.path.expanduser("~/vault"))
STATE_FILE = Path(os.path.expanduser("~/.hermes/data/logbook_state.json"))
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Tiers for categorisation
WATCH_DIRS = {
    "Knowledge": {"label": "📚 Knowledge", "detail": True},
    "Projects":  {"label": "📦 Projects",  "detail": True},
    "Wiki/entities":  {"label": "🏛️ Wiki Entities",  "detail": True},
    "Wiki/concepts":  {"label": "🧠 Wiki Concepts",  "detail": True},
    "Wiki/comparisons": {"label": "⚖️ Wiki Comparisons", "detail": True},
    "00-Inbox":  {"label": "📥 Inbox Captures", "detail": False},
    "Jornal/Ideas": {"label": "💡 New Ideas", "detail": True},
    "Jornal/Career": {"label": "💼 Career", "detail": True},
    "Kakurega Sector": {"label": "🏗️ Infra / Homelab", "detail": True},
}


def load_state():
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        # Convert lists back to sets for .add() to work
        for cat in state.get("tracked", {}):
            if isinstance(state["tracked"][cat], list):
                state["tracked"][cat] = set(state["tracked"][cat])
        return state
    return {"last_run": 0, "tracked": {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def scan_vault(since_mtime):
    """Return dict of category -> list of (path, mtime, is_new)"""
    changes = {}
    for cat, cfg in WATCH_DIRS.items():
        base = VAULT / cat
        if not base.exists():
            continue
        entries = []
        for p in sorted(base.rglob("*")):
            if p.is_dir() or p.name.startswith("."):
                continue
            if p.suffix not in (".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".sh"):
                continue
            stat = p.stat()
            mtime = stat.st_mtime
            if mtime > since_mtime:
                rel = p.relative_to(VAULT)
                entries.append((str(rel), mtime))
        if entries:
            changes[cat] = entries
    return changes


def format_digest(changes, state):
    now = time.time()
    lines = []
    lines.append(f"📋 **Vault Logbook** — {time.strftime('%A, %d %b %Y %H:%M')}")
    lines.append("")

    total = sum(len(v) for v in changes.values())
    if total == 0:
        return ""  # silent — nothing new

    for cat, cfg in WATCH_DIRS.items():
        entries = changes.get(cat)
        if not entries:
            continue
        lines.append(f"### {cfg['label']}")
        for relpath, mtime in sorted(entries, key=lambda x: x[0]):
            age = now - mtime
            if age < 3600:
                label = "🆕 just now"
            elif age < 7200:
                label = "🕐 <2h ago"
            elif age < 14400:
                label = "🕑 <4h ago"
            elif age < 43200:
                label = "🕒 <12h ago"
            elif age < 86400:
                label = "🕓 <1d ago"
            else:
                label = "🕔 older"

            if cat in state.get("tracked", {}) and relpath in state["tracked"].get(cat, []):
                # Already seen in a previous run — modified again
                prefix = "🔄 *updated*"
            else:
                prefix = "✨ *new*"

            if cfg["detail"]:
                lines.append(f"  {prefix} `{relpath}` {label}")
            else:
                lines.append(f"  {prefix} {Path(relpath).name} {label}")

        lines.append("")

    lines.append("---")
    return "\n".join(lines)


def main():
    state = load_state()
    since = state.get("last_run", time.time() - 86400)  # default: last 24h
    changes = scan_vault(since)
    digest = format_digest(changes, state)

    # Update state: remember what we've seen
    for cat, entries in changes.items():
        if cat not in state["tracked"]:
            state["tracked"][cat] = set()
        for relpath, _ in entries:
            state["tracked"][cat].add(relpath)
    # Convert sets to lists for JSON
    state["tracked"] = {k: list(v) for k, v in state["tracked"].items()}
    state["last_run"] = time.time()
    save_state(state)

    if digest:
        print(digest)


if __name__ == "__main__":
    main()
