#!/usr/bin/env python3
"""inbox-reminder.py — Weekly reminder of old inbox items.

Runs Monday 09:00 via cron (no_agent). Posts to Discord #announcements.
Silent when inbox is clean.
"""

from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/vault")))
INBOX = VAULT / "00-Inbox"
ARCHIVE_DAYS = 7


def age_in_days(path: Path) -> float:
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(tz=timezone.utc) - mtime).total_seconds() / 86400


def main():
    pending = []
    for p in sorted(INBOX.glob("*.md")):
        days = age_in_days(p)
        if days > ARCHIVE_DAYS:
            pending.append((p.name, int(days)))

    if not pending:
        return  # silent — nothing to remind about

    print(f"📥 **Inbox items needing attention ({len(pending)} older than {ARCHIVE_DAYS}d):**")
    for name, days in pending:
        print(f"- {name} — {days}d old")
    print("\n_Use the inbox or wiki-ingest channels to file them._")


if __name__ == "__main__":
    main()
