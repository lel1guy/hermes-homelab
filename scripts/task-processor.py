#!/usr/bin/env python3
"""task-processor.py — Scan vault for tasks, rebuild ToDo.md.

Runs nightly at 23:00 via cron (no_agent). Reads all .md files,
extracts open (- [ ]) and done (- [x]) tasks, groups by source folder,
flags stale tasks (7+ days untouched).
"""

import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/vault")))
TODO_FILE = VAULT / "Jornal" / "ToDo.md"

# Skip these directories
SKIP_DIRS = {
    "00-Inbox",
    "_hermes",
    "Private",
    "Wiki/raw",
    "Template",
    ".git",
    "Jornal",
}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(VAULT)
    for skip in SKIP_DIRS:
        if str(rel).startswith(skip):
            return True
    return False


def collect_tasks() -> dict:
    """Scan vault for tasks, return {category: [(task_text, file_path, mod_time, is_checked)]}"""
    tasks = defaultdict(list)

    for md_file in sorted(VAULT.rglob("*.md")):
        if should_skip(md_file):
            continue

        content = md_file.read_text(encoding="utf-8", errors="replace")
        rel_path = md_file.relative_to(VAULT)
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc)

        # Category from folder structure
        parts = rel_path.parts
        category = parts[0] if len(parts) > 1 else "Root"

        for line in content.split("\n"):
            line_stripped = line.strip()
            # Open task
            m = re.match(r"^\s*- \[ \]\s+(.+)", line)
            if m:
                tasks[category].append({
                    "text": m.group(1),
                    "file": str(rel_path),
                    "mtime": mtime,
                    "done": False,
                })
            # Done task
            m = re.match(r"^\s*- \[x\]\s+(.+)", line, re.IGNORECASE)
            if m:
                tasks[category].append({
                    "text": m.group(1),
                    "file": str(rel_path),
                    "mtime": mtime,
                    "done": True,
                })

    return tasks


def build_todo_md(tasks: dict) -> str:
    """Build the ToDo.md content from categorized tasks."""
    now = datetime.now(tz=timezone.utc)
    lines = [
        "# 📋 Task List",
        "",
        f"*Auto-generated: {now.strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
    ]

    # Sort categories, "Root" at the end
    sorted_cats = sorted(
        [c for c in tasks.keys() if c != "Root"],
        key=lambda c: c.lower()
    )
    if "Root" in tasks:
        sorted_cats.append("Root")

    total_open = 0
    total_done = 0

    for cat in sorted_cats:
        items = tasks[cat]
        open_items = [i for i in items if not i["done"]]
        done_items = [i for i in items if i["done"]]

        if not open_items and not done_items:
            continue

        total_open += len(open_items)
        total_done += len(done_items)

        lines.append(f"## 📁 {cat}")
        lines.append("")

        if open_items:
            for item in open_items:
                days_old = (now - item["mtime"]).days
                stale_mark = " ⚠️" if days_old >= 7 else ""
                lines.append(f"- [ ] {item['text']} — `{item['file']}`{stale_mark}")
        if done_items:
            lines.append("")
            for item in done_items:
                lines.append(f"- [x] ~{item['text']}~ — `{item['file']}`")

        lines.append("")

    # Summary
    lines.insert(3, f"**📊 {total_open} open · {total_done} completed**")
    lines.insert(4, "")

    return "\n".join(lines)


def main():
    tasks = collect_tasks()
    content = build_todo_md(tasks)
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    TODO_FILE.write_text(content)

    total = sum(len(items) for items in tasks.values())
    open_count = sum(1 for items in tasks.values() for i in items if not i["done"])
    print(f"📋 Rebuilt ToDo.md: {open_count} open tasks across {len(tasks)} categories")


if __name__ == "__main__":
    main()
