# Cron Schedule

All scheduled jobs running on KAIDO-01. Jobs run via Hermes Agent's built-in cron scheduler (not system cron).

## Active Jobs (21 total)

| # | Job | Schedule | Type | Deliver | Last Run |
|---|-----|----------|------|---------|----------|
| 1 | Export sessions to 00-Inbox | Every 30m | Script | Local | ✅ |
| 2 | System Health Report | Every 6h (`0 */6 * * *`) | Script | #sys-status | ✅ |
| 3 | Vault Logbook | Every 6h (`0 */6 * * *`) | Script | #logbook | ✅ |
| 4 | Syncthing Events | Every 6h (`0 */6 * * *`) | Script | #sys-status | ✅ |
| 5 | RSS Feeds | Every 4h (`15 */4 * * *`) | Script | #general | ✅ |
| 6 | Daily inbox processor | Daily 01:00 (`0 1 * * *`) | Script | #announcements | ✅ |
| 7 | Nightly Wiki Ingest & Lint | Daily 03:00 (`0 3 * * *`) | Script | #wiki-ingest | ✅ |
| 8 | Vault auto backup | Daily 05:00 (`0 5 * * *`) | Script | Local | ✅ |
| 9 | Morning briefing | Daily 08:00 (`0 8 * * *`) | LLM-driven | #announcements | ✅ |
| 10 | Daily Study Podcast | Daily 08:00 (`0 8 * * *`) | LLM-driven | Study channel | ✅ |
| 11 | Study Plan — Daily Reminder | Daily 08:30 (`30 8 * * *`) | LLM-driven | Study channel | ✅ |
| 12 | Daily Tech Tutor Quiz | Daily 09:00 (`0 9 * * *`) | LLM-driven | Study channel | ✅ |
| 13 | Weekly inbox reminder | Mon 09:00 (`0 9 * * 1`) | Script | #announcements | ✅ |
| 14 | Weekly inbox consolidation | Sun 10:00 (`0 10 * * 0`) | LLM-driven | #announcements | ✅ |
| 15 | Weekly vault stats | Sat 10:00 (`0 10 * * 6`) | LLM-driven | #announcements | ✅ |
| 16 | Study Plan — Weekly Review | Sat 18:00 (`0 18 * * 6`) | LLM-driven | Study channel | ✅ |
| 17 | Daily session knowledge extraction | Daily 20:00 (`0 20 * * *`) | LLM-driven | Local | ✅ |
| 18 | Nightly note processing | Daily 22:00 (`0 22 * * *`) | LLM-driven | Local | ✅ |
| 19 | Weekly stale knowledge check | Sun 22:00 (`0 22 * * 0`) | LLM-driven | #announcements | ✅ |
| 20 | Nightly task processing | Daily 23:00 (`0 23 * * *`) | Script | Local | ✅ |
| 21 | Hermes Daily Note | Daily 23:59 (`59 23 * * *`) | LLM-driven | Local | ✅ |

## Job Categories

### ⏰ Recurring Info Jobs

| # | Job | What It Does |
|---|-----|-------------|
| 2 | **System Health Report** | Reports disk usage, CPU load, memory, Tailscale status, service health to #sys-status |
| 3 | **Vault Logbook** | Detects new/changed files in vault, reports activity to #logbook |
| 4 | **Syncthing Events** | Monitors Syncthing sync events, reports to #sys-status |
| 5 | **RSS Feeds** | Fetches configured RSS feeds, posts new items to #general |
| 9 | **Morning Briefing** | Checks system health (uptime, disk, memory, Tailscale, services), reads today's tasks from vault daily note, reviews yesterday's progress, flags stale tasks and inbox items |
| 10 | **Daily Study Podcast** | Generates daily study podcast using edge-tts, posts audio to study channel |
| 11 | **Study Plan Reminder** | Calculates current week in study plan, picks one task to focus on, posts encouragement |
| 12 | **Daily Tech Tutor Quiz** | Generates daily tech quiz question using daily-tutor-quiz skill |
| 13 | **Weekly Inbox Reminder** | Lists inbox items older than 7 days that still need processing, posts to #announcements |
| 15 | **Weekly Vault Stats** | Reports vault statistics (files, changes, wiki activity) to #announcements |
| 16 | **Study Plan — Weekly Review** | Reviews progress across the study plan, suggests adjustments |

### 🗄️ Maintenance Jobs

| # | Job | What It Does |
|---|-----|-------------|
| 1 | **Export Sessions** | Polls Hermes session store, exports completed sessions to vault as markdown (quality-filtered: ≥3 user messages, non-cron) |
| 6 | **Daily Inbox Processor** | Archives inbox items > 7 days, purges items > 30 days. Silent when nothing to do. |
| 7 | **Nightly Wiki Ingest** | Runs vault-wiki-diff.py to detect new/changed files, then creates/updates Wiki entity pages with raw source archiving |
| 8 | **Vault Auto Backup** | Git-commits and pushes vault changes to GitHub private repo |
| 20 | **Nightly Task Processing** | Scans all vault notes for `- [ ]` tasks, rebuilds `Jornal/ToDo.md` grouped by source, flags tasks untouched for 7+ days |
| 21 | **Hermes Daily Note** | Writes auto-generated daily summary to `00-Inbox/Hermes Daily Notes/` with frontmatter, session log, tasks completed, and follow-ups |

### 🧠 Knowledge Pipeline

| # | Job | What It Does |
|---|-----|-------------|
| 14 | **Weekly Inbox Consolidation** | Consolidation pass — catches anything daily extraction missed, checks for duplicate Knowledge/ files, cross-references with Wiki ingest pipeline |
| 17 | **Daily Session Knowledge Extraction** | Reads 1-2 most recent unprocessed session exports, extracts educational content → Knowledge/, code snippets → Cheat Sheets/, config → Hermes/ |
| 18 | **Nightly Note Processing** | Reads today's user daily note, extracts code snippets → Knowledge/, learnings → Knowledge/, tasks → Projects/, ideas → Ideas/ |
| 19 | **Weekly Stale Knowledge Check** | Flags Knowledge/ files not modified in 90+ days, scans for broken [[wikilinks]], checks for orphan root files |

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
│  │ • backups    │  │ • Knowledge  │  └──────────────┘ │
│  └─────────────┘  │   Extraction  │                    │
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
