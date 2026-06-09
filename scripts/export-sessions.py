#!/usr/bin/env python3
"""
Export all Hermes sessions to markdown notes in vault/00-Inbox/
Tracks already-exported sessions by ID so it only adds new ones.
Runs silently on cron — only prints when there's new content.
"""

import json
import os
import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/vitor/vault"))
INBOX = VAULT / "00-Inbox" / "Sessions"
TRACKER_FILE = VAULT / "_hermes" / "Scripts" / ".session_export_tracker.json"

SOURCE_LABELS = {
    "cli": "CLI",
    "discord": "Discord",
    "telegram": "Telegram",
    "webgui": "Web GUI",
    "whatsapp": "WhatsApp",
    "slack": "Slack",
    "gateway": "Gateway",
    "api": "API",
}


def get_hermes_sessions() -> list[dict]:
    """Export all sessions from Hermes as JSONL and extract messages."""
    result = subprocess.run(
        ["hermes", "sessions", "export", "/tmp/hermes_sessions_export.jsonl"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"ERROR: hermes sessions export failed: {result.stderr}", file=sys.stderr)
        return []

    export_file = Path("/tmp/hermes_sessions_export.jsonl")
    if not export_file.exists():
        print("ERROR: export file not created", file=sys.stderr)
        return []

    sessions = []
    for line in export_file.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        sessions.append(d)

    return sessions


def load_tracker() -> dict:
    if TRACKER_FILE.exists():
        try:
            return json.loads(TRACKER_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"exported_sessions": {}}


def save_tracker(tracker: dict):
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False))


def sanitize_for_filename(s: str, max_len: int = 55) -> str:
    s = s.strip().lower()[:60]
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s[:max_len].rstrip('-')


def source_emoji(source: str) -> str:
    return {
        "cli": "💻",
        "discord": "💬",
        "telegram": "📱",
        "webgui": "🌐",
        "whatsapp": "📞",
        "slack": "🔷",
        "gateway": "📡",
        "api": "🔌",
    }.get(source, "📄")


def parse_ts(ts_val: float | str | None) -> datetime | None:
    """Parse a timestamp that might be a Unix float or ISO string."""
    if ts_val is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts_val), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        pass
    try:
        return datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass
    return None


def make_session_note(session: dict) -> tuple[str, str]:
    sid = session["id"]
    source = session.get("source", "cli")
    title = session.get("title") or ""
    messages = session.get("messages", [])
    started_at = session.get("started_at", "")
    ended_at = session.get("ended_at", "")

    # Derive title from first user message if no title set
    if not title or title == "-":
        for m in messages:
            if m.get("role") in ("user", "human"):
                content = (m.get("content") or "").strip()
                if content:
                    title = content[:80].replace("\n", " ")
                    break
    if not title or title == "-":
        title = "Hermes Session"

    # Determine timestamp from started_at, first message, or fallback
    dt = None
    if started_at:
        dt = parse_ts(started_at)
    if dt is None and messages:
        dt = parse_ts(messages[0].get("timestamp"))
    if dt is None:
        dt = datetime.now(tz=timezone.utc)

    date_str = dt.strftime("%Y-%m-%d %H:%M")
    file_ts = dt.strftime("%Y%m%d_%H%M%S")

    safe_title = sanitize_for_filename(title)
    filename = f"{file_ts}_{safe_title}.md" if safe_title else f"{file_ts}_hermes-session.md"

    emoji = source_emoji(source)
    src_label = SOURCE_LABELS.get(source, source.capitalize())

    # Stats
    user_msgs = sum(1 for m in messages if m.get("role") in ("user", "human"))
    asst_msgs = sum(1 for m in messages if m.get("role") in ("assistant", "agent"))
    total_msgs = session.get("message_count", len(messages))

    lines = [
        "---",
        f"created: {date_str}",
        f"source: {source}",
        f"session_id: {sid}",
        f'title: "{title}"',
        "---",
        "",
        f"# {emoji} {title}",
        "",
        f"**Source:** {src_label}  |  **Date:** {date_str}",
        "",
    ]

    if total_msgs:
        lines.append(f"*{total_msgs} mensagens — {user_msgs} suas, {asst_msgs} do Hermes*")
        lines.append("")

    lines.append("---")
    lines.append("")

    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content") or ""
        timestamp = m.get("timestamp", "")

        # Skip system/tool messages
        if role in ("tool", "system"):
            continue

        ts_str = ""
        if timestamp:
            t = parse_ts(timestamp)
            if t:
                ts_str = f" *({t.strftime('%H:%M:%S')})*"

        if role in ("user", "human"):
            heading = f"### 👤 Você{ts_str}"
        elif role in ("assistant", "agent"):
            heading = f"### 🤖 Hermes{ts_str}"
        else:
            heading = f"### ⚙️ {role.capitalize()}{ts_str}"

        lines.append(heading)
        lines.append("")

        # Add tool call note for assistant messages
        tool_calls = m.get("tool_calls")
        if role in ("assistant", "agent") and tool_calls:
            tools_used = []
            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "unknown")
                tools_used.append(name)
            if tools_used:
                lines.append(f"> 🔧 *Ferramentas: `{'`, `'.join(tools_used)}`*")
                lines.append("")

        # Content — strip excessive whitespace
        if content:
            lines.append(content)
        else:
            lines.append("*[vazio]*")

        lines.append("")

    # Footer
    if ended_at:
        end_dt = parse_ts(ended_at)
        if end_dt:
            duration = end_dt - dt if dt else None
            dur_str = ""
            if duration:
                total_min = int(duration.total_seconds() / 60)
                if total_min > 0:
                    dur_str = f" — duração: {total_min}min"
            lines.append(f"*Sessão encerrada em {end_dt.strftime('%Y-%m-%d %H:%M')}{dur_str}*")
            lines.append("")

    lines.append("---")
    lines.append(f"*Exportado de `{sid}` em {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return filename, "\n".join(lines)


def is_worth_exporting(session: dict) -> bool:
    """Quality filter — skip things that shouldn't land in the inbox."""
    source = session.get("source", "")

    # Skip cron/internal plumbing sessions entirely
    if source == "cron":
        return False

    # Skip trivial sessions with fewer than 3 user messages
    messages = session.get("messages", [])
    user_msgs = sum(1 for m in messages if m.get("role") in ("user", "human"))
    if user_msgs < 3:
        return False

    return True


def main():
    INBOX.mkdir(parents=True, exist_ok=True)
    tracker = load_tracker()
    exported = tracker.get("exported_sessions", {})
    new_count = 0
    updated_count = 0
    skipped_count = 0

    sessions = get_hermes_sessions()
    if not sessions:
        print("No sessions found or export failed.")
        return

    for session in sessions:
        sid = session.get("id")
        if not sid:
            continue

        # Quality filter
        if not is_worth_exporting(session):
            skipped_count += 1
            continue

        messages = session.get("messages", [])
        current_msg_count = len(messages)

        record = exported.get(sid)

        if record:
            # Already exported — only re-export if messages changed
            if record.get("message_count", 0) >= current_msg_count:
                continue
            # Messages grew — reuse tracked file path, overwrite it
            dest = VAULT / record["file"]
            updated_count += 1
        else:
            # New session — generate filename with collision avoidance
            filename, content = make_session_note(session)
            dest = INBOX / filename
            counter = 1
            while dest.exists():
                dest = INBOX / f"{dest.stem}_{counter}.md"
                counter += 1
            new_count += 1

        filename, content = make_session_note(session)

        # Only write if content actually changed (content diff)
        existing_content = dest.read_text() if dest.exists() else None
        if existing_content == content:
            # Same content despite message count change — still update tracker
            if sid in exported:
                exported[sid]["message_count"] = current_msg_count
            continue

        dest.write_text(content)
        exported[sid] = {
            "file": str(dest.relative_to(VAULT)),
            "exported_at": datetime.now().isoformat(),
            "source": session.get("source", "cli"),
            "message_count": current_msg_count,
        }

    tracker["exported_sessions"] = exported
    tracker["last_run"] = datetime.now().isoformat()
    tracker["total_exported"] = len(exported)
    save_tracker(tracker)

    # Produce a meaningful summary when there's action
    parts = []
    if new_count > 0:
        parts.append(f"{new_count} nova(s)")
    if updated_count > 0:
        parts.append(f"{updated_count} atualizada(s)")
    if parts:
        print(f"📥 {' + '.join(parts)} em 00-Inbox/ ({len(exported)} total, {skipped_count} ignoradas)")


if __name__ == "__main__":
    main()
