#!/usr/bin/env python3
"""inbox-processor.py — Archive old items, purge very old items.

Runs nightly via cron (no_agent mode). Reports action taken to Discord.
Archives items >7d, purges items >30d. Silent when nothing to do.
"""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/vault")))
INBOX = VAULT / "00-Inbox"
ARCHIVE = INBOX / "Archive"
ARCHIVE_DAYS = 7
PURGE_DAYS = 30


def age_in_days(path: Path) -> float:
    """Return the age of a file in days."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(tz=timezone.utc) - mtime).total_seconds() / 86400


def main():
    # Collect all markdown files in the inbox root (not in subdirectories)
    items = [p for p in INBOX.iterdir() if p.suffix == ".md" and p.is_file()]

    archived = 0
    archived_names = []
    purged = 0
    purged_names = []

    for item in items:
        days = age_in_days(item)
        if days > PURGE_DAYS:
            item.unlink()
            purged += 1
            purged_names.append(item.name)
        elif days > ARCHIVE_DAYS:
            ARCHIVE.mkdir(parents=True, exist_ok=True)
            dest = ARCHIVE / item.name
            shutil.move(str(item), str(dest))
            archived += 1
            archived_names.append(item.name)

    if archived or purged:
        report_parts = []
        if archived:
            report_parts.append(f"🗂️ Archived {archived} items ({', '.join(archived_names[:5]}{"…" if archived > 5 else ""}))")
        if purged:
            report_parts.append(f"🗑️ Purged {purged} items ({', '.join(purged_names[:5]}{"…" if purged > 5 else ""}))")
        print(" | ".join(report_parts))


if __name__ == "__main__":
    main()
