#!/usr/bin/env python3
"""logbook.py — Track vault file changes and report to #logbook.

Runs every 6h via cron (no_agent). Detects new/modified files in key
vault directories. Silent when nothing new.
"""

import json
import os
from datetime import datetime
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/vault")))
STATE_FILE = Path(os.path.expanduser("~/.hermes/cron/output/logbook_state.json"))

WATCHED = [
    "Knowledge",
    "Projects",
    "Wiki/entities",
    "Wiki/concepts",
    "Jornal/Ideas",
]


def get_file_snapshot(paths: list[str]) -> dict:
    """Build a dict of relative_path -> (mtime, size) for all .md files."""
    snap = {}
    for folder in paths:
        target = VAULT / folder
        if not target.exists():
            continue
        for f in target.rglob("*.md"):
            rel = f.relative_to(VAULT)
            snap[str(rel)] = (f.stat().st_mtime, f.stat().st_size)
    return snap


def main():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    previous = {}
    if STATE_FILE.exists():
        try:
            previous = json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    current = get_file_snapshot(WATCHED)

    new_files = []
    changed_files = []

    for path, (mtime, size) in current.items():
        if path not in previous:
            new_files.append(path)
        elif previous[path][0] != mtime or previous[path][1] != size:
            changed_files.append(path)

    stale = [p for p in previous if p not in current]

    if not new_files and not changed_files and not stale:
        return  # silent

    print(f"📋 **Vault Logbook — {datetime.now().strftime('%Y-%m-%d %H:%M')}**")
    if new_files:
        print(f"\n**✨ New files ({len(new_files)}):**")
        for f in new_files[:10]:
            print(f"- `{f}`")
        if len(new_files) > 10:
            print(f"  _…and {len(new_files) - 10} more_")
    if changed_files:
        print(f"\n**📝 Updated ({len(changed_files)}):**")
        for f in changed_files[:10]:
            print(f"- `{f}`")
        if len(changed_files) > 10:
            print(f"  _…and {len(changed_files) - 10} more_")
    if stale:
        print(f"\n**🗑️ Removed ({len(stale)}):**")
        for f in stale[:5]:
            print(f"- `{f}`")

    STATE_FILE.write_text(json.dumps(current, indent=2))


if __name__ == "__main__":
    main()
