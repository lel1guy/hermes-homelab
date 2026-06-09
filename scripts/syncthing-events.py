#!/usr/bin/env python3
"""syncthing-events.py — Poll Syncthing events and report changes.

Polls Syncthing's /rest/events API. Tracks last event ID in state file.
Reports: sync completed, conflicts, errors, device connect/disconnect.
Silent when nothing new (empty stdout = no delivery).
Deduplicates consecutive identical messages to reduce noise.

Requires: syncthing config.xml with apikey.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import urllib.request

SYNCTHING_URL = "http://localhost:8384"
STATE = Path(os.path.expanduser("~/.hermes/syncthing_state.json"))


def get_api_key():
    """Read API key from Syncthing config."""
    config_path = Path(os.path.expanduser("~/.config/syncthing/config.xml"))
    if not config_path.exists():
        return None
    raw = config_path.read_text()
    # Simple XML parsing without external deps
    start = raw.find("<apikey>")
    if start == -1:
        return None
    start += len("<apikey>")
    end = raw.find("</apikey>", start)
    if end == -1:
        return None
    return raw[start:end]


def api_get(endpoint):
    """Make a Syncthing API GET request."""
    key = get_api_key()
    if not key:
        return None
    req = urllib.request.Request(
        f"{SYNCTHING_URL}{endpoint}",
        headers={"X-API-Key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def load_state():
    if STATE.exists():
        with open(STATE) as f:
            return json.load(f)
    return {"last_event_id": 0, "last_run": 0}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f)


def format_events(events):
    """Format new Syncthing events into a digest. Deduplicates consecutive identical lines."""
    lines = []
    now = time.strftime("%H:%M")

    for ev in events:
        ev_type = ev.get("type", "")
        data = ev.get("data", {})

        if ev_type == "FolderErrors":
            folder = data.get("folder", "?")
            errors = data.get("errors", [])
            for err in errors[:3]:
                lines.append(f"  \u26a0\ufe0f **Folder Error** \u2014 `{folder}`: {err.get('path', '?')} \u2014 {err.get('error', '?')}")

        elif ev_type == "FolderCompletion":
            # Completion events are noisy and redundant with FolderSummary
            pass

        elif ev_type == "FolderSummary":
            folder = data.get("folder", "?")
            summary = data.get("summary", {})
            state = summary.get("state", "?")
            if state == "idle":
                need_bytes = summary.get("needBytes", 0)
                need_files = summary.get("needFiles", 0)
                if need_bytes == 0 and need_files == 0:
                    lines.append(f"  \u2705 **Sync complete** \u2014 `{folder}` is up to date")
                else:
                    lines.append(f"  \U0001f504 **Syncing** `{folder}` \u2014 {need_files} files ({need_bytes} bytes) remaining")

        elif ev_type == "DeviceConnected":
            name = data.get("deviceName", data.get("addr", ""))
            short = data.get("id", "?")[:12]
            lines.append(f"  \U0001f50c **Device connected** \u2014 `{name}` (`{short}\u2026`)")

        elif ev_type == "DeviceDisconnected":
            name = data.get("deviceName", data.get("addr", ""))
            short = data.get("id", "?")[:12]
            err = data.get("error", "")
            emoji = "\u26a0\ufe0f" if err else "\U0001f50c"
            msg = f"  {emoji} **Device disconnected** \u2014 `{name}` (`{short}\u2026`)"
            if err:
                msg += f" \u2014 {err}"
            lines.append(msg)

        elif ev_type == "LocalIndexUpdated":
            folder = data.get("folder", "?")
            items = data.get("items", 0)
            if items == 0:
                lines.append(f"  \U0001f4c4 **Local changes detected** \u2014 `{folder}`: scanning\u2026")

    if not lines:
        return None

    # Deduplicate consecutive identical messages (same folder events fire repeatedly)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    header = f"## \U0001f4e1 Syncthing \u2014 update at {now}\n"
    return header + "\n" + "\n".join(deduped) + "\n"


def main():
    state = load_state()
    since_id = state.get("last_event_id", 0)

    # Get events since last seen
    events = api_get(f"/rest/events?since={since_id}&limit=50")
    if events is None:
        # Try system status as fallback
        status = api_get("/rest/system/status")
        if status:
            my_id = status.get("myID", "")[:12]
            print(f"## \U0001f4e1 Syncthing \u2014 status at {time.strftime('%H:%M')}")
            print(f"  \u2139\ufe0f **Device ID:** `{my_id}\u2026`")
            print(f"  \u2139\ufe0f Try again next cycle \u2014 API unavailable now")
        return

    if not events:
        return  # Nothing new

    # Track the latest ID
    max_id = max(ev.get("id", 0) for ev in events)
    if max_id > 0:
        state["last_event_id"] = max_id
    state["last_run"] = time.time()
    save_state(state)

    output = format_events(events)
    if output:
        print(output)


if __name__ == "__main__":
    main()
