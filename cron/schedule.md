# Cron Schedule

All scheduled jobs running on KAIDO-01. Jobs run via Hermes Agent's built-in cron scheduler (not system cron).

## Summary

| # | Job | Schedule | Type | Output |
|---|-----|----------|------|--------|
| 1 | Morning Briefing | Daily 08:00 | LLM-driven | Discord #announcements |
| 2 | Study Plan — Daily Reminder | Daily 09:00 | LLM-driven | Discord DM |
| 3 | Weekly Inbox Reminder | Mon 09:00 | Script | Discord #announcements |
| 4 | Weekly Inbox Knowledge Extraction | Sun 10:00 | LLM-driven | Discord #announcements |
| 5 | System Health Report | Every 4h | Script | Discord #sys-status |
| 6 | Vault Logbook | Every 6h | Script | Discord #logbook |
| 7 | RSS Feeds | Every 4h (:15) | Script | Discord #general |
| 8 | Syncthing Events | Hourly | Script | Discord #sys-status |
| 9 | Export Sessions to Vault | Every 30m | Script | Local (vault) |
| 10 | Vault Auto Backup | Daily 05:00 | Script | Local (git push) |
| 11 | Nightly Note Processing | Daily 22:00 | LLM-driven | Vault updates |
| 12 | Nightly Task Processing | Daily 23:00 | Script | Vault ToDo.md |
| 13 | Hermes Daily Note | Daily 23:59 | LLM-driven | Vault daily note |
| 14 | Nightly Wiki Ingest | Daily 03:00 | LLM-driven + Script | Wiki updates |

## Detailed Job Descriptions

### ⏰ Recurring Info Jobs

| ID | Job | What It Does |
|----|-----|-------------|
| 1 | **Morning Briefing** | Checks system health (uptime, disk, memory, Tailscale, services), reads today's tasks from vault daily note, reviews yesterday's progress, flags stale tasks and inbox items |
| 3 | **Weekly Inbox Reminder** | Lists inbox items older than 7 days that still need processing, posts to announce |
| 4 | **Weekly Inbox Knowledge Extraction** | Scans inbox for substantive content, files learnings to Knowledge/Projects/Wiki, reports summary |
| 5 | **System Health Report** | Reports disk usage, CPU load, memory, Tailscale status, service health to #sys-status |
| 6 | **Vault Logbook** | Detects new/changed files in vault, reports activity to #logbook |
| 7 | **RSS Feeds** | Fetches configured RSS feeds, posts new items to #general |
| 8 | **Syncthing Events** | Monitors Syncthing sync events, reports to #sys-status |

### 🗄️ Maintenance Jobs

| ID | Job | What It Does |
|----|-----|-------------|
| 9 | **Export Sessions** | Polls Hermes session store, exports completed sessions to vault as markdown (quality-filtered: ≥3 user messages, non-cron) |
| 10 | **Vault Auto Backup** | Git-commits and pushes vault changes to GitHub private repo |
| 12 | **Nightly Task Processing** | Scans all vault notes for `- [ ]` tasks, rebuilds `Jornal/ToDo.md` grouped by source, flags tasks untouched for 7+ days |
| 13 | **Hermes Daily Note** | Writes auto-generated daily summary to `00-Inbox/Hermes Daily Notes/` with frontmatter, session log, tasks completed, and follow-ups |

### 🧠 Knowledge Pipeline

| ID | Job | What It Does |
|----|-----|-------------|
| 2 | **Study Plan Reminder** | Calculates current week in 16-week cert plan, picks one task to focus on, posts encouragement |
| 5 | **Weekly Study Review** | Reviews progress across the study plan, suggests adjustments |
| 11 | **Nightly Note Processing** | Reads today's daily note, extracts code snippets → Knowledge/, learnings → Knowledge/, tasks → Projects/, ideas → Ideas/ |
| 14 | **Nightly Wiki Ingest** | Uses vault-wiki-diff.py to detect new/changed files, then creates/updates Wiki entity pages with raw source archiving |

## Architecture

```
┌───────────────────────────────────────────────────────┐
│              Hermes Cron Scheduler                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Script Jobs  │  │ LLM-driven   │  │ Hybrid       │ │
│  │ (no_agent)   │  │ Jobs         │  │ (script+LLM) │ │
│  │              │  │              │  │              │ │
│  │ • sys-status │  │ • Briefing   │  │ • Wiki       │ │
│  │ • rss-feeds  │  │ • Daily Note │  │   Ingest     │ │
│  │ • backups    │  │ • Knowledge  │  │              │ │
│  └─────────────┘  │   Extraction  │  └──────────────┘ │
│                    └──────────────┘                    │
└───────────────────────────────────────────────────────┘
```

- **Script jobs** run headless — no LLM tokens consumed
- **LLM-driven jobs** get a prompt and full agent capabilities
- **Hybrid jobs** use a script for data collection then an LLM agent for processing

## How It Works

The scheduler is built into Hermes Agent. Jobs are defined in `~/.hermes/cron/jobs.json` and managed via the `cronjob` tool. Each job has:
- A `schedule` (cron expression or interval)
- A `prompt` (for LLM-driven jobs) or `script` (for script jobs)
- A `deliver` target (Discord channel, local file, etc.)
- Optional `skills`, `model`, `workdir`, `profile` overrides