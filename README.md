# hermes-homelab

> Production-grade Hermes AI Agent homelab — Discord ops, automated knowledge management, cron pipelines, and systemd services running on Fedora Linux.

Built by [@lel1guy](https://github.com/lel1guy) from Quarteira, Algarve, Portugal, running on KAIDO-01 in the Kakurega Sector homelab.

---

## Overview

This repository documents a real, running deployment of [Hermes Agent](https://hermes-agent.nousresearch.com) on a self-hosted Linux server. It covers configuration, automation scripts, Discord integration, and Obsidian vault workflows — all managed through cron-driven pipelines.

The homelab processes session exports, RSS feeds, vault backups, wiki updates, task tracking, daily study podcasts, tech quizzes, and system health monitoring on a daily schedule.

---

## Contents

### Configuration

| File | Purpose |
|------|---------|
| `config.yaml` | Hermes Agent configuration (redacted for public — secrets in .env) |
| `SOUL.md` | Agent personality definition (Karasu persona — 184 lines) |
| `vault-structure/AGENTS.md` | Vault rules, folder roles, processing pipelines (203 lines) |

### Automation Scripts

All scripts live in `scripts/` and run on cron schedules:

| Script | Purpose | Schedule |
|--------|---------|----------|
| `export-sessions.py` | Export Hermes sessions to Obsidian vault | Every 30 min |
| `inbox-processor.py` | Archive/purge inbox items by age | Daily 01:00 |
| `inbox-reminder.py` | Remind about stale inbox items | Weekly Mon 09:00 |
| `task-processor.py` | Rebuild task list from vault notes | Daily 23:00 |
| `rss-feeds.py` | Fetch and file RSS feed articles | Every 4 hours |
| `vault-backup.sh` | Backup vault to external storage | Daily 05:00 |
| `vault-wiki-diff.py` | Detect and report wiki page changes | Every 6 hours |
| `syncthing-events.py` | Process Syncthing sync events | Every 6 hours |
| `logbook.py` | Generate vault change log reports | Every 6 hours |
| `sys-status.sh` | System health snapshot (disk, memory, uptime) | Every 6 hours |
| `ccna-processor.py` | Fetch YouTube transcripts → CCNA concept notes | On demand |
| `feeds.json` | *(removed — feed sources now configurable in rss-feeds.py)* | — |

### Systemd Services

Managed via `systemctl` on Fedora:

| Service | Description |
|---------|-------------|
| `services/hermes-gateway.service` | Hermes Agent gateway daemon (API endpoint) |
| `services/hermes-dashboard.service` | Hermes web dashboard UI |
| `services/hermes-webui.service` | Hermes web interface |

> **Note:** Systemd services are optionally deployed. The homelab currently runs Hermes via the built-in scheduler, not system-level services.

### Discord Integration

| Resource | Description |
|----------|-------------|
| `discord/channel-prompts.md` | Channel-specific prompt definitions for 9 Discord channels, including full `#hermes-knowledge` extraction workflow |
| `config.yaml` (discord section) | Channel ID config, auto-thread settings, history backfill |

### Cron Jobs

| Resource | Description |
|----------|-------------|
| `cron/schedule.md` | Full cron schedule reference — **21 active jobs** with job IDs, intervals, and categories |

### LLM-Driven Jobs (7)

The scheduler runs 21 total jobs. 7 are LLM-driven (consume tokens):

| Job | Schedule | Purpose |
|-----|----------|---------|
| Morning Briefing | Daily 08:00 | System health + tasks + stale item review |
| Daily Study Podcast | Daily 08:00 | Audio podcast generation via edge-tts |
| Study Plan — Daily Reminder | Daily 08:30 | Weekly study plan progress nudges |
| Daily Tech Tutor Quiz | Daily 09:00 | Daily tech quiz question |
| Daily Session Knowledge Extraction | Daily 20:00 | Extract learnings from recent sessions |
| Nightly Note Processing | Daily 22:00 | Process user daily notes |
| Weekly Stale Knowledge Check | Sun 22:00 | Audit Knowledge/ for stale/broken files |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| OS | Fedora Linux 44 |
| Agent | Hermes Agent v0.16.0 |
| LLM | DeepSeek V4 Flash |
| Database | PostgreSQL 18 (local + Honcho memory layer) |
| Automation | Python 3.11, Bash, systemd, cron |
| Vault | Obsidian + Syncthing sync |
| Integrations | Discord, RSS/Atom feeds |
| Memory | Honcho (semantic memory layer) |

---

## Hardware

| Component | Spec |
|-----------|------|
| Machine | KAIDO-01 (Kakurega Sector) |
| CPU | Intel i5-6200U (4 cores) @ 2.30GHz |
| RAM | 8 GB |
| Storage | 240 GB SSD |
| GPU | Intel HD Graphics 520 |
| Network | Tailscale mesh (torii.net) |

---

## Architecture

```
Discord ──> Hermes Gateway ──> LLM (DeepSeek) ──> Hermes Agent
                         │                           │
                         └──> cron jobs    ────> Obsidian Vault
                                               ┌──── R|W
                                               ▼
                                         PostgreSQL
                                         (Honcho + apps)
```

Daily pipelines:
- **Session export** (every 30min) — save conversation history to vault
- **Inbox processing** (daily 01:00) — archive/cleanse inbox items
- **Wiki ingest** (daily 03:00) — process Knowledge/ into Wiki/
- **Task processing** (daily 23:00) — rebuild ToDo.md from all notes
- **Knowledge extraction** (daily 20:00) — extract learnings from sessions to Knowledge/
- **Study pipeline** (daily 08:00-09:30) — podcast, reminders, tech quizzes
- **RSS feeds** (every 4h) — pull articles from security/tech sources
- **System health** (every 6h) — disk, memory, uptime monitoring
- **Weekly maintenance** (Sundays) — consolidation, stale checks, vault stats

---

## Getting Started

This repo is a reference/blueprint for your own Hermes Agent homelab. To adapt it:

```bash
# 1. Install Hermes Agent
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 2. Copy and adapt config
cp config.yaml ~/.hermes/config.yaml
# Edit: add your API keys, paths, Discord channel IDs

# 3. Copy scripts
cp -r scripts/ ~/.hermes/scripts/

# 4. Set up systemd services (Linux, optional)
cp services/*.service /etc/systemd/system/
systemctl daemon-reload

# 5. Configure cron jobs (see cron/schedule.md for reference)
```

---

## Status

Running 24/7 on KAIDO-01 (Fedora 44, 8GB RAM, 240GB SSD). **21 active cron jobs.** Also hosts Honcho (AI memory layer with pgvector) and Open Notebook (AI research notebook) as sibling Docker Compose stacks. See [lel1guy/homelab](https://github.com/lel1guy/homelab) for the full infrastructure overview. Actively maintained — new scripts and automations added as the homelab evolves.
