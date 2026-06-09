#!/usr/bin/env python3
"""
Weekly inbox reminder — runs Monday 09:00 via cron.

Scans 00-Inbox/ (root captures + Sessions/) for items older than 7 days that
are still unarchived. Silent when nothing needs attention.
"""

import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/vitor/vault"))
INBOX_SESSIONS = VAULT / "00-Inbox" / "Sessions"
INBOX_ROOT = VAULT / "00-Inbox"
ARCHIVE = INBOX_SESSIONS / "Archive"

REMINDER_AFTER_DAYS = 7


def parse_created_from_frontmatter(content: str) -> datetime | None:
    m = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})", content, re.MULTILINE)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def get_file_age(filepath: Path) -> timedelta | None:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    created = parse_created_from_frontmatter(content)
    if created:
        return datetime.now(tz=timezone.utc) - created
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
    return datetime.now(tz=timezone.utc) - mtime


def scan_directory(directory: Path, exclude_dirs: set[Path] | None = None) -> list[Path]:
    """Scan a directory for .md files, excluding specific subdirectories."""
    if not directory.exists():
        return []
    exclude_dirs = exclude_dirs or set()
    files = []
    for f in sorted(directory.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        if f.parent in exclude_dirs:
            continue
        files.append(f)
    return files


def main():
    now = datetime.now(tz=timezone.utc)
    stale = []

    # Scan Sessions/ (auto-generated exports)
    session_files = scan_directory(INBOX_SESSIONS, exclude_dirs={ARCHIVE})

    # Scan root of 00-Inbox/ (manual captures)
    root_files = []
    if INBOX_ROOT.exists():
        for f in sorted(INBOX_ROOT.iterdir()):
            if not f.is_file() or not f.name.endswith(".md"):
                continue
            root_files.append(f)

    all_files = session_files + root_files

    for f in all_files:
        age = get_file_age(f)
        if age is None:
            continue

        if age.days >= REMINDER_AFTER_DAYS:
            created_date = (now - age).strftime("%Y-%m-%d")
            stale.append(f"  \u2022 {f.name} ({created_date}, {age.days}d)")

    if not stale:
        return  # Silent — nothing to report

    header = f"\U0001f4cb **Inbox Reminder** \u2014 {len(stale)} item(s) older than {REMINDER_AFTER_DAYS}d:\n"
    note = "\nReview and archive manually, or the nightly processor will handle it."
    print(header + "\n".join(stale) + note)


if __name__ == "__main__":
    main()
