#!/usr/bin/env python3
"""
Daily inbox processor — runs nightly via cron.

Processes items in both:
  - 00-Inbox/ (root-level raw captures, manual forwards)
  - 00-Inbox/Sessions/ (auto-generated session exports)

Excludes:
  - 00-Inbox/Hermes Daily Notes/ (generated nightly)
  - 00-Inbox/Sessions/Archive/ (already archived)

- Items > 30 days old → deleted (with report)
- Items > 7 days old → moved to 00-Inbox/Archive/
- Prints a summary of what was done (only when there's action)
"""

import os
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/vitor/vault"))
INBOX_SESSIONS = VAULT / "00-Inbox" / "Sessions"
INBOX_ROOT = VAULT / "00-Inbox"
ARCHIVE = INBOX_SESSIONS / "Archive"
HERMES_DAILY = VAULT / "00-Inbox" / "Hermes Daily Notes"

RETENTION_DAYS_WARN = 7   # Move to archive
RETENTION_DAYS_PURGE = 30 # Delete permanently


def parse_created_from_frontmatter(content: str) -> datetime | None:
    """Try to extract `created: YYYY-MM-DD HH:MM` from markdown frontmatter."""
    m = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})", content, re.MULTILINE)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def get_file_age(filepath: Path) -> timedelta | None:
    """Get the age of a file based on frontmatter (preferred) or mtime."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    created = parse_created_from_frontmatter(content)
    if created:
        return datetime.now(tz=timezone.utc) - created
    # Fallback to mtime
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
    return datetime.now(tz=timezone.utc) - mtime


def format_age(age: timedelta) -> str:
    days = age.days
    if days < 1:
        return f"{age.seconds // 3600}h"
    return f"{days}d"


def scan_directory(directory: Path, exclude_dirs: set[Path] | None = None) -> list[Path]:
    """Scan a directory for .md files, excluding specific subdirectories."""
    if not directory.exists():
        return []
    files = []
    exclude_dirs = exclude_dirs or set()
    for f in sorted(directory.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        # Check if any parent of this file is in the exclude list
        if f.parent in exclude_dirs:
            continue
        files.append(f)
    return files


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    archived = []
    purged = []
    errors = []
    now = datetime.now(tz=timezone.utc)

    # Scan Sessions/ (auto-generated exports)
    session_files = scan_directory(INBOX_SESSIONS, exclude_dirs={ARCHIVE})

    # Scan root of 00-Inbox/ (manual captures), excluding subdirectories
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

        # Purge: > 30 days old
        if age.days >= RETENTION_DAYS_PURGE:
            try:
                f.unlink()
                purged.append(f.name)
            except OSError as e:
                errors.append(f"Failed to purge {f.name}: {e}")
            continue

        # Archive: > 7 days old
        if age.days >= RETENTION_DAYS_WARN:
            dest = ARCHIVE / f.name
            try:
                shutil.move(str(f), str(dest))
                archived.append(f.name)
            except OSError as e:
                errors.append(f"Failed to archive {f.name}: {e}")

    # Only print when there's something to report
    parts = []
    if archived:
        parts.append(f"\U0001f4e6 {len(archived)} archived \u2192 Archive/")
    if purged:
        parts.append(f"\U0001f5d1\ufe0f {len(purged)} removed (> {RETENTION_DAYS_PURGE}d)")
    if errors:
        for err in errors:
            parts.append(f"\u26a0\ufe0f {err}")

    if parts:
        print(" | ".join(parts))
    # else: silent — nothing to process


if __name__ == "__main__":
    main()
