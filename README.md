# 🏠🤖 Kakurega Sector — Hermes Homelab

> The AI agent infrastructure running my homelab from Quarteira, Algarve 🇵🇹

Built by [@lel1guy](https://github.com/lel1guy) — always tinkering, always learning.

---

This repo documents my **Hermes Agent** setup — a self-hosted AI assistant that manages my Obsidian knowledge vault, monitors system health, integrates with Discord for operations, and runs automated pipelines via cron. Everything runs on **KAIDO-01**, my Fedora Linux homelab server.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      KAIDO-01 (Fedora Linux)                 │
│                                                              │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │  Hermes Gateway   │     │   Hermes Web UI   │              │
│  │  (Discord ops)    │     │   (Browser GUI)   │              │
│  │  :systemd service │     │   :8787           │              │
│  └────────┬─────────┘     └────────┬─────────┘              │
│           │                        │                        │
│  ┌────────▼────────────────────────▼──────────────────┐     │
│  │              Hermes Agent (DeepSeek V4 Flash)      │     │
│  │  • ~20 cron jobs • 12 custom scripts • 900+ skills │     │
│  │  • Obsidian vault bridge • Persistent memory       │     │
│  └────────┬────────────────────────────┬──────────────┘     │
│           │                            │                     │
│  ┌────────▼────────┐        ┌─────────▼──────────┐         │
│  │  Obsidian Vault  │        │   n8n Webhook      │         │
│  │  (Knowledge Mgmt)│        │   (Automation)      │         │
│  └─────────────────┘        └────────────────────┘         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Systemd Services                                   │    │
│  │  • hermes-gateway.service  (Discord/API gateway)    │    │
│  │  • hermes-webui.service    (Browser interface)      │    │
│  │  • hermes-dashboard.service (Remote backend)        │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## ✨ What It Does

| What | How |
|------|-----|
| **🤖 AI Agent** | Hermes Agent (Nous Research) — DeepSeek V4 Flash, persistent memory, 150 max turns |
| **💬 Discord Ops** | Free-response channels, per-channel prompts, threaded convos, auto-reactions |
| **⏰ Cron Automation** | ~20 scheduled jobs — vault backups, wiki ingest, morning briefings, RSS, system health, study reminders |
| **📜 Custom Scripts** | 12 Python/bash scripts for session export, inbox management, task processing, backup, sync monitoring |
| **📚 Knowledge Mgmt** | Obsidian vault with automated wiki ingest, daily note processing, inbox pipeline, session archiving |
| **🔧 Systemd Services** | 3 user services with auto-restart and graceful shutdown |
| **🔗 Integrations** | Discord, n8n webhook, Google Workspace, Tailscale, Syncthing |
| **🧠 Skills Library** | 900+ skills (cybersecurity, devops, creative, coding) auto-synced from community repos |

## 📂 What's in Here

```
hermes-homelab/
├── README.md                    # You are here
├── config.yaml                  # Hermes Agent config (secrets redacted)
├── SOUL.md                      # Agent personality definition
├── services/                    # Systemd user service files
│   ├── hermes-gateway.service
│   ├── hermes-webui.service
│   └── hermes-dashboard.service
├── scripts/                     # Custom vault automation scripts
│   ├── export-sessions.py       # Export Hermes sessions to vault
│   ├── inbox-processor.py       # Archive/purge inbox items
│   ├── inbox-reminder.py        # Weekly old-item reminder
│   ├── logbook.py               # Vault change detection
│   ├── rss-feeds.py             # RSS feed fetcher
│   ├── syncthing-events.py      # Monitor Syncthing syncs
│   ├── sys-status.sh            # System health report
│   ├── task-processor.py        # Nightly task list rebuild
│   ├── vault-backup.sh          # Git-based vault backup
│   └── vault-wiki-diff.py       # Wiki content change detection
├── cron/
│   └── schedule.md              # Full cron schedule documentation
├── discord/
│   └── channel-prompts.md       # Discord channel behavior config
├── skills/                      # Custom-authored skills
│   └── dogfood/
│       ├── SKILL.md
│       └── references/
└── vault-structure/
    └── AGENTS.md                # Vault organization rules
```

## 🛠️ Tech Stack

| Layer | What I Use |
|-------|-----------|
| **OS** | Fedora Linux 44 |
| **AI Agent** | [Hermes Agent](https://hermes-agent.nousresearch.com) (Nous Research) |
| **LLM** | DeepSeek V4 Flash |
| **Vault** | Obsidian (Syncthing-synced) |
| **Automation** | n8n, cron, custom Python/bash |
| **Networking** | Tailscale (mesh VPN) |
| **Orchestration** | systemd (user services) |
| **Platform** | Discord, webhook |

## 🔒 Security

- All API keys, tokens, and secrets are **redacted** from this repo
- `.env` and credential stores are **never committed**
- `config.yaml` is a reference template — actual secrets use environment variables
- Private vault content is excluded

---

*Built from scratch, running 24/7 in a closet in Quarteira. Started as "let's see if I can make this work" and turned into the backbone of my digital life.*
