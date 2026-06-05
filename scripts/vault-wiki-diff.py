#!/usr/bin/env python3
"""vault-wiki-diff.py — Detect new/changed vault content for wiki ingest.

Outputs JSON to stdout for the nightly wiki cron job (LLM-driven) to consume.
Tracks file SHA256 hashes to detect changes.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/vault")))
STATE_FILE = Path(os.path.expanduser("~/.hermes/cron/output/vault_wiki_diff_state.json"))

# Directories to watch
WATCH = [
    "Knowledge",
    "Projects",
    "Jornal/Ideas",
]

# Skip patterns
SKIP_PATTERNS = [
    ".sync-conflict-",
    "_index.md",
    "SCHEMA.md",
    "log.md",
]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_index() -> dict:
    """Build {relative_path: sha256} for all watched files."""
    idx = {}
    for folder in WATCH:
        target = VAULT / folder
        if not target.exists():
            continue
        for f in target.rglob("*.md"):
            rel = str(f.relative_to(VAULT))
            if any(skip in rel for skip in SKIP_PATTERNS):
                continue
            idx[rel] = sha256_of(f)
    return idx


def main():
    current = build_index()

    previous = {}
    if STATE_FILE.exists():
        try:
            previous = json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    new_files = [p for p in current if p not in previous]
    changed_files = [p for p in current if p in previous and current[p] != previous[p]]
    stale_files = [p for p in previous if p not in current]

    result = {
        "timestamp": datetime.now().isoformat(),
        "tracked": len(current),
        "new": sorted(new_files),
        "changed": sorted(changed_files),
        "stale": sorted(stale_files),
        "summary": {
            "new": len(new_files),
            "changed": len(changed_files),
            "stale": len(stale_files),
        }
    }

    # Save state for next run
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(current, indent=2))

    # Output JSON — consumed by the LLM cron job that follows
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
