#!/usr/bin/env python3
"""
vault-wiki-diff.py — Scan vault for new/changed content vs Wiki/raw/ articles.

Outputs a structured JSON report with three sections:
  - new:       files in vault not yet in raw/
  - changed:   files in vault that differ from raw/ (different SHA256)
  - stale:     raw/ articles whose vault source no longer exists
  - unchanged: files already synced (count only, for the summary)

This script is the data-collection layer for the nightly wiki ingest cron job.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

VAULT = os.environ.get("VAULT_PATH", "/home/vitor/vault")
WIKI = os.environ.get("WIKI_PATH", f"{VAULT}/Wiki")

# Directories to IGNORE when scanning the whole vault
IGNORE_DIRS = {
    "_hermes",      # Hermes internal files
    "Wiki",         # The wiki itself — self-referential
    "Private",      # Sensitive — never expose
    "Template",     # Templates, not content
    ".trash",       # Obsidian trash/deleted notes
    "00-Inbox",     # Session exports — handled by weekly inbox review cron
}

# For Jornal/Daily, only consider files newer than this many days
DAILY_LOOKBACK_DAYS = 7


def sha256_file(path: str) -> str:
    """Compute SHA256 of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_raw_frontmatter(path: str) -> dict:
    """Parse frontmatter from a raw/ article. Returns {source_url, sha256}."""
    meta = {"source_url": None, "sha256": None}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return meta

    # Match frontmatter between --- markers
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return meta

    for line in m.group(1).split("\n"):
        line = line.strip()
        if line.startswith("source_url:"):
            meta["source_url"] = line.split(":", 1)[1].strip()
        elif line.startswith("sha256:"):
            meta["sha256"] = line.split(":", 1)[1].strip()

    return meta


def build_raw_index() -> dict:
    """Build a map: vault_relative_path -> {sha256, raw_file_path} from raw/ articles."""
    raw_dir = os.path.join(WIKI, "raw", "articles")
    index = {}

    if not os.path.isdir(raw_dir):
        return index

    for fname in os.listdir(raw_dir):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(raw_dir, fname)
        meta = parse_raw_frontmatter(fpath)
        vault_path = meta.get("source_url") or ""
        # Strip "vault:" prefix
        if vault_path.startswith("vault:"):
            vault_path = vault_path[len("vault:"):]
        if vault_path:
            index[vault_path] = {
                "sha256": meta.get("sha256"),
                "raw_file": fpath,
            }
    return index


def scan_vault_files() -> list[dict]:
    """Walk the entire vault, skipping IGNORE_DIRS, returning {rel_path, abs_path, mtime}."""
    files = []
    now = datetime.now(timezone.utc).timestamp()
    lookback_secs = DAILY_LOOKBACK_DAYS * 86400

    for entry in os.listdir(VAULT):
        rel_dir = os.path.join(VAULT, entry)
        if not os.path.isdir(rel_dir):
            continue
        if entry in IGNORE_DIRS:
            continue

        is_daily = entry == "Jornal"

        for root, dirs, fnames in os.walk(rel_dir):
            # When walking Jornal/, skip the root Jornal/ itself
            if is_daily and root == rel_dir:
                continue

            for fname in fnames:
                if not fname.endswith(".md"):
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, VAULT)

                # Jornal/Daily: only recent notes
                if is_daily and "Daily" in rel_path.split(os.sep):
                    try:
                        mtime = os.path.getmtime(abs_path)
                    except OSError:
                        continue
                    if now - mtime > lookback_secs:
                        continue

                files.append({
                    "rel_path": rel_path,
                    "abs_path": abs_path,
                })

    return files


def main():
    raw_index = build_raw_index()

    # Scan vault files
    vault_files = scan_vault_files()

    new_files = []
    changed_files = []
    unchanged_count = 0

    for vf in vault_files:
        rp = vf["rel_path"]
        try:
            current_sha = sha256_file(vf["abs_path"])
        except Exception:
            continue

        if rp in raw_index:
            stored_sha = raw_index[rp].get("sha256")
            if stored_sha and stored_sha == current_sha:
                unchanged_count += 1
            else:
                changed_files.append({
                    "rel_path": rp,
                    "abs_path": vf["abs_path"],
                    "old_sha256": stored_sha,
                    "new_sha256": current_sha,
                })
        else:
            new_files.append({
                "rel_path": rp,
                "abs_path": vf["abs_path"],
                "sha256": current_sha,
            })

    # Find stale raw/ articles (source gone from vault)
    vault_paths = {vf["rel_path"] for vf in vault_files}
    stale_articles = []
    for rp, ri in raw_index.items():
        if rp not in vault_paths:
            stale_articles.append({
                "rel_path": rp,
                "raw_file": ri["raw_file"],
                "sha256": ri.get("sha256"),
            })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "new": len(new_files),
            "changed": len(changed_files),
            "stale": len(stale_articles),
            "unchanged": unchanged_count,
            "total_vault_scanned": len(vault_files),
            "total_raw_articles": len(raw_index),
        },
        "new": new_files,
        "changed": changed_files,
        "stale": stale_articles,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
