# Hermes Homelab 🏠🤖

**Production-grade AI agent infrastructure running on a Fedora Linux homelab.**

This repository documents my **Hermes Agent** setup — a self-hosted AI assistant that manages my Obsidian knowledge vault, monitors system health, integrates with Discord for operations, and runs automated pipelines via cron. It's the brain behind **Kakurega Sector** (`KAIDO-01`), my personal homelab.

> **What recruiters will see:** A homelab running a production AI agent with real Discord ops, automated knowledge management pipelines, systemd-managed services, and Python automation — demonstrating Linux sysadmin, infrastructure-as-code, Python scripting, and operational monitoring skills.

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
│  │              Hermes Agent (DeepSeek V4)             │     │
│  │  • 14 cron jobs • 12 custom scripts • 900+ skills  │     │
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

## ✨ Features

| Category | Details |
|----------|---------|
| **🤖 AI Agent** | Hermes Agent (Nous Research) — DeepSeek V4 Flash, 150 max turns, persistent memory |
| **💬 Discord Ops** | Free-response channels, channel-specific prompts, threaded conversations, automatic reactions |
| **⏰ Cron Automation** | 14 scheduled jobs — vault backup, wiki ingest, morning briefings, RSS feeds, system health, study reminders |
| **📜 Custom Scripts** | 12 Python/bash scripts for vault session export, task processing, inbox management, Syncthing monitoring |
| **📚 Knowledge Mgmt** | Obsidian vault with automated wiki ingest, daily note processing, inbox pipeline, session archiving |
| **🔧 Systemd Services** | 3 user services with auto-restart, graceful shutdown, health monitoring |
| **🔗 Integrations** | Discord, n8n webhook, Google Workspace (Gmail/Calendar/Drive), Tailscale, Syncthing |
| **🧠 Skills Library** | 900+ skills (cybersecurity, devops, creative, research, coding) auto-synced from community repos |

## 📂 Repository Structure

```
hermes-homelab/
├── README.md                    # You are here
├── config.yaml                  # Hermes Agent config (secrets redacted)
├── SOUL.md                      # Agent persona definition
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

## 🚀 Getting Started

This is a **reference setup** — you don't just clone and run (it's deeply tied to my homelab). But if you want to use Hermes Agent yourself:

1. **Install Hermes**: Follow the [official docs](https://hermes-agent.nousresearch.com/docs)
2. **Configure**: Copy `config.yaml` as a starting template, fill in your own API keys
3. **Add services**: Copy systemd files, adjust paths
4. **Set up vault**: Use `vault-structure/AGENTS.md` as a template for your knowledge management
5. **Deploy scripts**: Adapt the Python scripts to your paths

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **OS** | Fedora Linux 44 |
| **AI Agent** | [Hermes Agent](https://hermes-agent.nousresearch.com) (Nous Research) |
| **LLM** | DeepSeek V4 Flash (via DeepSeek API) |
| **Vault** | Obsidian (Syncthing-synced) |
| **Automation** | n8n, cron, custom Python/bash |
| **Networking** | Tailscale (mesh VPN) |
| **Orchestration** | systemd (user services) |
| **Platform** | Discord, webhook |

## 📊 Key Metrics

- **900+** installed skills (755 cybersecurity) — synced from community repositories
- **14** automated cron jobs running daily/weekly
- **3** systemd services with auto-restart
- **12** custom Python/bash automation scripts
- **1** Obsidian vault with wiki, projects, daily notes, and inbox pipeline

## 🔒 Security Notes

- All API keys, tokens, and secrets are **redacted** from this repo
- The `.env` file and credential stores are **never committed**
- `config.yaml` is a reference template — actual secrets use environment variables
- Private vault content is excluded

## 📸 In Action

> *The Hermes Dashboard showing system status and conversation history.*
> *Automated morning briefings delivered to Discord.*
> *Wiki pages auto-ingested from YouTube videos and web articles.*

## 📝 License

MIT — Feel free to use this as inspiration for your own setup.

---

*Built by [@lel1guy](https://github.com/lel1guy) — always tinkering, always learning.*