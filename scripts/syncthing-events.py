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
    return {"last_id": 0, "last_messages": []}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    state = load_state()
    last_id = state.get("last_id", 0)
    last_messages = state.get("last_messages", [])

    events = api_get(f"/rest/events?since={last_id}")
    if events is None:
        return

    if not events:
        return  # silent

    new_last_id = max(e["id"] for e in events)
    relevant = []

    for e in events:
        typ = e.get("type", "")
        data = e.get("data", {})
        msg = None

        if typ == "StateChanged":
            folder = data.get("folder", "?")
            to = data.get("to", "")
            if to == "syncing":
                msg = f"🔄 Syncing `{folder}`…"
            elif to == "idle":
                msg = f"✅ Synced `{folder}`"
        elif typ == "RemoteDownloadProgress":
            pass  # too noisy
        elif typ == "DeviceConnected":
            dev = data.get("deviceName", data.get("device", "?"))
            msg = f"🔗 Device connected: `{dev}`"
        elif typ == "DeviceDisconnected":
            dev = data.get("deviceName", data.get("device", "?"))
            msg = f"🔌 Device disconnected: `{dev}`"
        elif typ == "FolderErrors":
            folder = data.get("folder", "?")
            errors = data.get("errors", [])
            if errors:
                msg = f"❌ Errors in `{folder}`: {len(errors)} issue(s)"
        elif typ == "DeviceRejected":
            dev = data.get("device", "?")
            msg = f"⚠️ Device rejected: `{dev}`"

        if msg and msg not in last_messages[-5:]:
            relevant.append(msg)

    if relevant:
        for msg in relevant:
            print(msg)

    state["last_id"] = new_last_id
    state["last_messages"] = (last_messages + relevant)[-10:]
    save_state(state)


if __name__ == "__main__":
    main()
