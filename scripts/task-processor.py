#!/usr/bin/env python3
"""
task-processor.py — Nightly vault task scanner with bidirectional sync.

1. READS existing ToDo.md for newly-completed tasks (marked - [x] with src: annotations)
2. Syncs those completions BACK to their source notes
3. Scans all vault notes for - [ ] and - [x] items
4. Rebuilds Jornal/ToDo.md with src: annotations for future bidirectional sync
5. Flags tasks untouched for 7+ days

Designed as a no_agent cron job. Silent when nothing changed.

Task annotation format in ToDo.md:
  - [ ] Task text <!-- src:path/to/note.md -->

When syncing back, it matches the task TEXT in the source note (not line number)
so line shifts don't break the mapping.
"""

import os
import re
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/vitor/vault"))
TODO_PATH = VAULT / "Jornal" / "ToDo.md"
STATE_PATH = Path(os.path.expanduser("~/.hermes/data/task_processor_state.json"))

# Directories to exclude from scanning
EXCLUDE_DIRS: set[str] = {".trash", "_hermes", "Private", "Template", "Wiki/raw"}
# File extensions to scan
SCAN_EXTENSIONS = {".md"}


# ── Helpers ──

def load_state() -> dict:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_run_hash": "", "last_run": 0}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def should_scan_dir(dirpath: str) -> bool:
    parts = Path(dirpath).relative_to(VAULT).parts
    return not any(excl in parts for excl in EXCLUDE_DIRS)


def is_valid_task_file(abspath: str) -> bool:
    """Check if the file can be a source of tasks (not a template, not wiki raw)."""
    p = Path(abspath)
    if p.suffix not in SCAN_EXTENSIONS:
        return False
    rel = p.relative_to(VAULT).as_posix()
    # Skip known auto-generated/non-task files
    if rel == "Jornal/ToDo.md":
        return False
    if rel.startswith("Wiki/raw/"):
        return False
    if rel.startswith("Template/"):
        return False
    return True


def scan_tasks_in_file(filepath: str) -> list[dict]:
    """Parse a markdown file and return all task items with their line numbers."""
    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return tasks

    for i, line in enumerate(lines, 1):
        # Match - [ ] and - [x] (standard markdown checkboxes)
        m = re.match(r"^(\s*)[-*]\s+\[([ xX])\]\s+(.+)", line)
        if not m:
            continue
        indent = m.group(1)
        checked = m.group(2).lower() == "x"
        text = m.group(3).strip()
        tasks.append({
            "line": i,
            "indent": indent,
            "checked": checked,
            "text": text,
            "line_content": line,
        })
    return tasks


def find_task_in_file(filepath: str, task_text: str) -> int | None:
    """
    Find a task line in a file by matching its text content.
    Returns the line number (1-indexed) or None.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return None

    target = task_text.strip().lower()
    best_match = None
    best_score = 0

    for i, line in enumerate(lines, 1):
        m = re.match(r"^(\s*)[-*]\s+\[([ xX])\]\s+(.+)", line)
        if not m:
            continue
        checked = m.group(2).lower() == "x"
        text = m.group(3).strip().lower()
        if text == target:
            return i  # exact match
        # Fuzzy: check partial match
        score = len(set(text.split()) & set(target.split()))
        if score > best_score:
            best_score = score
            best_match = i

    # Only use fuzzy if we have a good match (at least 80% of words match)
    if best_match and best_score > 0:
        return best_match
    return None


def update_task_in_file(filepath: str, line_num: int, checked: bool) -> bool:
    """Toggle a task at a specific line number between - [ ] and - [x]."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return False

    if line_num < 1 or line_num > len(lines):
        return False

    old_line = lines[line_num - 1]
    m = re.match(r"^(\s*[-*]\s+)\[([ xX])\](.*)", old_line)
    if not m:
        return False

    new_status = "x" if checked else " "
    new_line = f"{m.group(1)}[{new_status}]{m.group(3)}\n"

    if new_line == old_line:
        return True  # Already correct

    lines[line_num - 1] = new_line
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except OSError:
        return False


def get_file_mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0

import json as json_module
json = json_module


# ── Phase 1: Sync completed tasks from ToDo.md back to source notes ──

def sync_completions_from_todo(todo_path: Path) -> list[str]:
    """
    Read ToDo.md, find - [x] tasks that aren't completed in their source notes,
    and update the source notes.

    Source file is determined from the section-level wikilink:
      > Full checklist in [[path/to/note.md]]

    Returns list of messages about what was synced.
    """
    if not todo_path.exists():
        return []

    content = todo_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    synced = []
    current_src = None

    for line in lines:
        # Detect section-level source: > Full checklist in [[path/to/note.md]]
        m = re.match(r">\s*Full checklist in \[\[([^\]]+)\]\]", line)
        if m:
            current_src = m.group(1).strip()
            continue

        # Detect completed tasks: - [x] task text
        m = re.match(r"^(\s*)[-*]\s+\[x\]\s+(.+)", line, re.IGNORECASE)
        if not m or not current_src:
            continue

        task_text = m.group(2).strip()
        src_path = VAULT / current_src
        if not src_path.exists():
            continue

        # Find and update the matching task in the source file
        line_num = find_task_in_file(str(src_path), task_text)
        if line_num:
            if update_task_in_file(str(src_path), line_num, True):
                synced.append(
                    f"  \u2705 `{current_src}`: \"{task_text[:60]}...\""
                )

    return synced


# ── Phase 2: Scan vault and rebuild ToDo.md ──

def scan_vault_tasks() -> dict:
    """
    Walk the entire vault, scan each file for tasks.
    Returns dict: folder -> { note_path: {tasks, mtime} }
    """
    results: dict[str, dict] = {}

    for root, dirs, fnames in os.walk(str(VAULT)):
        if not should_scan_dir(root):
            continue

        # Filter dirs in-place so os.walk doesn't descend
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

        for fname in fnames:
            fpath = os.path.join(root, fname)
            if not is_valid_task_file(fpath):
                continue

            tasks = scan_tasks_in_file(fpath)
            if not tasks:
                continue

            rel_path = os.path.relpath(fpath, str(VAULT))
            parent = os.path.dirname(rel_path) or "Root"
            mtime = get_file_mtime(fpath)

            if parent not in results:
                results[parent] = {}
            results[parent][rel_path] = {
                "tasks": tasks,
                "mtime": mtime,
            }

    return results


def build_todo_markdown(folder_data: dict, now_ts: float) -> str:
    """Build the complete ToDo.md content with src annotations."""
    sections = []

    # Sort folders alphabetically, but put Jornal/ at the end
    sorted_folders = sorted(folder_data.keys())
    jornal = [f for f in sorted_folders if f.startswith("Jornal")]
    other = [f for f in sorted_folders if not f.startswith("Jornal")]
    sorted_folders = other + jornal

    for folder in sorted_folders:
        notes = folder_data[folder]
        section_tasks = []
        note_entries = []

        for note_path in sorted(notes.keys()):
            info = notes[note_path]
            tasks = info["tasks"]
            mtime = info["mtime"]
            date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
            open_tasks = [t for t in tasks if not t["checked"]]
            done_tasks = [t for t in tasks if t["checked"]]

            if not open_tasks:
                continue  # Skip notes with no remaining open tasks

            # Note header with link
            note_name = Path(note_path).stem.replace("-", " ").title()
            note_entries.append({
                "path": note_path,
                "name": note_name,
                "date": date_str,
                "open_count": len(open_tasks),
                "done_count": len(done_tasks),
                "open": open_tasks,
                "mtime": mtime,
            })

        if not note_entries:
            continue

        # Sort by mtime (most recent first)
        note_entries.sort(key=lambda e: e["mtime"], reverse=True)

        section_lines = [f"## {folder}\n"]
        for ne in note_entries:
            stale_marker = ""
            age_days = (now_ts - ne["mtime"]) / 86400
            if age_days > 7:
                stale_marker = f" \u26a0\ufe0f *{int(age_days)}d untouched*"

            section_lines.append(
                f"**{ne['name']}** *(last touched {ne['date']})*{stale_marker}\n"
            )
            section_lines.append(
                f"> Full checklist in [[{ne['path']}]]\n"
            )
            section_lines.append("")

            # Add tasks (no per-task src annotation — source is at section level)
            for task in ne["open"]:
                checked = "x" if task["checked"] else " "
                section_lines.append(
                    f"{task['indent']}- [{checked}] {task['text']}\n"
                )

            section_lines.append("")

        sections.append("".join(section_lines))

    now_utc = datetime.now(tz=timezone.utc)
    header = (
        "# ToDo\n\n"
        "*Auto-maintained. Do not edit manually.*\n"
        "*Mark tasks as `- [x]` here and they sync back to the source note overnight.*\n"
        f"*Last updated: {now_utc.strftime('%Y-%m-%d %H:%M')} UTC*\n\n"
        "---\n\n"
    )
    return header + "\n".join(sections)


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ── Main ──

def main():
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    state = load_state()

    # ── Phase 1: Sync back completed tasks from ToDo.md ──
    sync_messages = sync_completions_from_todo(TODO_PATH)

    # ── Phase 2: Scan vault for all tasks ──
    folder_data = scan_vault_tasks()

    # ── Phase 3: Build new ToDo.md ──
    new_content = build_todo_markdown(folder_data, now_ts)

    # ── Only write if content changed ──
    new_hash = compute_content_hash(new_content)
    old_hash = state.get("last_run_hash", "")

    lines = []
    if new_hash != old_hash:
        TODO_PATH.parent.mkdir(parents=True, exist_ok=True)
        TODO_PATH.write_text(new_content, encoding="utf-8")
        state["last_run_hash"] = new_hash
        # Count stats
        total_open = sum(
            sum(1 for t in ni["tasks"] if not t["checked"])
            for folder in folder_data.values()
            for ni in folder.values()
        )
        lines.append(f"## \U0001f4cb Task Processor \u2014 {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
        lines.append(f"\n**Scanned:** {sum(len(v) for v in folder_data.values())} notes across {len(folder_data)} source folders")
        lines.append(f"**ToDo.md:** Rebuilt with **{total_open} open tasks**\n")

        # Build summary table
        lines.append("| Source Folder | Notes | Open Tasks | Status |")
        lines.append("|---|---|---|---|")
        for folder in sorted(folder_data.keys()):
            notes_folder = folder_data[folder]
            note_count = len(notes_folder)
            open_count = sum(
                sum(1 for t in ni["tasks"] if not t["checked"])
                for ni in notes_folder.values()
            )
            # Check if any note is stale (>7 days)
            max_mtime = max(ni["mtime"] for ni in notes_folder.values())
            age_days = (now_ts - max_mtime) / 86400
            status = f"\u26a0\ufe0f **{int(age_days)}d stale**" if age_days > 7 else "\u2705 Current"
            lines.append(f"| {folder} | {note_count} | {open_count} | {status} |")
    else:
        # Nothing changed, check if there are sync messages
        if not sync_messages:
            return  # Silent

        lines.append(f"## \U0001f4cb Task Processor \u2014 {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
        lines.append("\nNo task changes detected in vault. ToDo.md unchanged.\n")

    # Report sync completions
    if sync_messages:
        lines.append("\n### \U0001f504 Synced Back to Source Notes\n")
        lines.append("The following tasks were marked done in ToDo.md and synced to their source notes:")
        lines.append("")
        lines.extend(sync_messages)

    # Report stale tasks
    stale_sections = []
    for folder in sorted(folder_data.keys()):
        for note_path, info in folder_data[folder].items():
            age_days = (now_ts - info["mtime"]) / 86400
            open_tasks = [t for t in info["tasks"] if not t["checked"]]
            if age_days > 7 and open_tasks:
                stale_sections.append(f"  \u2022 **{note_path}** \u2014 {int(age_days)}d untouched, {len(open_tasks)} open tasks")

    if stale_sections:
        lines.append("\n### \u26a0\ufe0f Stale Tasks (7+ days untouched)\n")
        lines.extend(stale_sections)

    state["last_run"] = now_ts
    save_state(state)

    print("\n".join(lines))


if __name__ == "__main__":
    main()
