# Vault Structure & Hermes Rules

## Folder Roles

| Folder | Role | Hermes Behavior |
|--------|------|-----------------|
| `00-Inbox/` | Raw captures from Discord/WhatsApp/CLI | Default write target for new captures. Prompt user to process items older than 7 days. |
| `Knowledge/` | Evergreen reference | File extracted knowledge here. Create new notes, update existing ones, link related topics. |
| `Projects/` | Active projects | Each subfolder is a project. Respect existing project notes. Create/update project-tracker notes. |
| `_hermes/Assistant/` | Hermes living files | `context.md`, `preferences.md`, `environment.md`, plus `logs/issues-fixes-log.md`. Editable from Obsidian — these are the stable reference tier of the memory pipeline. Memory promotes here when MEMORY.md hits ~67% capacity. |
| `Kakurega Sector/` | Infrastructure & homelab | Ongoing setup docs, machine specs, network configs. Read-only reference — do not reorganize. |
| `Game Dev/` | Active game projects — design docs, build notes, asset inventory | One subfolder per game. Read existing notes before creating new ones. Cross-link with `[[wikilinks]]`. No code in vault — code lives on machines and GitHub. Keep README.md status table current. |
| `Jornal/` | Timeline / daily capture | Append-only. Do not rearrange existing notes. |
| `Jornal/Daily/` | User's personal daily scratchpad — **DEPRECATED** | No longer used. Daily notes pipeline decommissioned. |
| `Jornal/Ideas/` | Project seeds | Read for context when brainstorming. File new ideas here. |
| `Jornal/Prompts/` | Prompt engineering notes | Reference for prompt patterns. |
| `Jornal/_Archive/Career/` | Job search & career (archived) | Read for context. Do not share outside vault. |
| `Jornal/ToDo.md` | Auto-maintained task list | Rebuild nightly with open tasks from all notes, grouped by source folder. Do not edit manually. |
| `Wiki/` | LLM Wiki (Karpathy pattern) | Persistent compounding knowledge base. Hermes maintains entities/, concepts/, comparisons/, queries/. Schema at `SCHEMA.md`, index at `index.md`, log at `log.md`. Raw sources in `raw/`. |
| `Private/` | Sensitive data | **Never expose** to external APIs, web search, or Discord/WhatsApp responses. Do not read for context in non-private queries. |
| `Template/` | Note templates | Use when creating new notes of a given type. |

## Processing Rules

### Inbox Processing (`00-Inbox/`)

| Folder | Role |
|--------|------|
| `00-Inbox/` (root) | Raw captures — manual forwards from Discord/WhatsApp/CLI |
| `00-Inbox/Sessions/` | Auto-generated session exports (every 30 min) |

### Sources
- **Session exports**: Every 30 min via `export-sessions.py` → `00-Inbox/Sessions/` — only if the session has ≥3 user messages and is NOT a cron/scheduled job session. Ongoing sessions overwrite their tracked file when new messages arrive.
- **Raw captures**: Manual forwards from Discord/WhatsApp/CLI land in `00-Inbox/` at the root level.

### Quality Filters (`export-sessions.py`)
- Cron/internal plumbing sessions are **skipped** entirely
- Sessions with fewer than 3 user messages are **skipped** (trivial)
- Already-exported sessions are **re-exported only if messages changed** (overwrites tracked file, no versioning)

### Retention Policy
- **> 7 days old**: Auto-archived to `00-Inbox/Sessions/Archive/` by the nightly processor
- **> 30 days old**: Auto-deleted by the nightly processor
- **Weekly reminder** (Monday 09:00 → Discord #ann): Lists items still pending older than 7 days

### Nightly Cron: `inbox-processor.py`
- Runs daily at 01:00
- Archives items > 7 days → `00-Inbox/Sessions/Archive/`
- Purges items > 30 days
- Silent when nothing to do; reports to Discord #announcements when action taken

### #hermes-knowledge Channel (Discord)
- Anyone can post a URL (article, doc, YouTube video, GitHub repo) in the channel
- Hermes automatically extracts the content and files it to the correct Knowledge/ folder following the folder rules
- Always reads existing notes first to avoid duplicates
- Creates `[[wikilinks]]` to related notes
- Also saves a raw copy to `00-Inbox/` for archival
- Posts a summary back to the channel of what was filed and where

### Daily Session Knowledge Extraction (20:00)
- Reads 1-2 most recent unprocessed session exports from `00-Inbox/Sessions/`
- Extracts educational content → `Knowledge/<topic>/`
- Extracts code snippets → `Knowledge/Cheat Sheets/`
- Extracts config/setup → `Knowledge/Hermes/` or relevant topic
- Silent when nothing to extract; reports summary to local

### Weekly Inbox Consolidation (Sunday 10:00)
- Consolidation pass — catches anything the daily extraction missed
- Checks for duplicate/overlapping Knowledge/ files to merge
- Cross-references with Wiki ingest pipeline
- Reports summary to Discord #announcements

### Weekly Stale Knowledge Check (Sunday 22:00)
- Flags Knowledge/ files not modified in 90+ days
- Scans for broken `[[wikilinks]]`
- Checks for orphan root files that should be in topic folders
- Verifies `_index.md` accuracy against actual file tree
- Reports to Discord #announcements, silent when clean

## Knowledge Folder Rules

The `Knowledge/` folder is the **evergreen reference** — curated, organised, and maintained by the extraction pipeline.

### Folder structure (current as of repo snapshot)

| Folder | Focus |
|--------|-------|
| `Bash/` | Shell scripting, commands, automation |
| `CCNA/` | Networking fundamentals |
| `Cheat Sheets/` | Quick-reference cards for tools/languages |
| `Docker/` | Containerization concepts |
| `Domotics/` | Smart home, building automation (PT-PT) |
| `Estatistica/` | University statistics (PT) |
| `Game Design/` | Narrative design, worldbuilding |
| `Game-Programming-Patterns/` | Nystrom's design patterns — 19 patterns for game dev |
| `Game-Theory-Predictive-History/` | Predictive history, institutional analysis, game theory |
| `Git/` | Version control, Git basics, branching, PRs |
| `Godot/` | Godot Engine 4.7 — full extracted docs + C# curriculum |
| `Hermes/` | Hermes Agent config & skills |
| `Homelab/` | Self-hosted infrastructure — hardware, services, backups |
| `Intro to Programming/` | Python fundamentals |
| `Machine Learning/` | ML algorithms and local LLM inference |
| `Patterns/` | Cross-domain patterns and dyslexia-accessible formatting |
| `Procedural Animation/` | Procedural animation techniques for game dev |
| `References/` | Ops School sysadmin/ops curriculum |
| `Relational Databases/` | SQL & PostgreSQL |
| `Space/` | Astronomy, cosmology, Fermi Paradox, astrobiology |

### Extraction rules
- **Code snippets/CLI commands** → `Knowledge/Cheat Sheets/`
- **Educational content / tutorials** → `Knowledge/<topic>/` with proper wikilinks
- **Setup instructions / config** → `Knowledge/Hermes/` if Hermes-related, else relevant topic
- **Course notes** → topic folder. Full-length courses at root.
- **Research / reference** → standalone note at root with wikilinks
- **Project tasks** → `Projects/` (not Knowledge/)
- **Ideas** → `Jornal/Ideas/` if concept, `Projects/` if actionable
- **Wiki-specific content** → leave for the nightly Wiki ingest (03:00)
- Do NOT create duplicate notes — read existing ones first
- Notes must be evergreen — no "today", "yesterday", "in this session" references
- Use `[[wikilinks]]` to connect related notes

### Health checks
- Weekly stale audit (Sun 22:00): flags files not modified in 90+ days
- Weekly broken-wikilink scan (Sun 22:00): reports `[[links]]` to non-existent notes
- `_index.md` should be updated when new folders or major files are added

## Wiki Update Policy

- When a source is ingested, update relevant entity/concept/comparison pages and log the action
- `Wiki/index.md`: master content catalog — update with every new/updated page
- `Wiki/log.md`: chronological action log — append after every operation
- Wiki pages are LLM-distilled from sources and user conversation.

## General Rules

- Never expose `Private/` contents in any external response
- Use `[[wikilinks]]` to connect related notes
- Respect existing file structure — do not rename or move user-created folders
- Infrastructure naming: refer to `Kakurega Sector/KODŌ_NAMING_SYSTEM.md` for hostname conventions
- When in doubt, ask before acting

---

## Hermes Internals (`_hermes/`)

The `_hermes/` directory bridges Hermes and this vault:

| File / Folder | Type | Purpose |
|--------------|------|---------|
| `_hermes/MEMORY.md` | Real file (inverted symlink) | Hermes persistent memory. Editing this updates what Hermes remembers across sessions. |
| `_hermes/Skills/` | External skills dir | Skills are `SKILL.md` files. Hermes loads them automatically. |
| `_hermes/Scripts/` | Vault-managed scripts | Bash/Python scripts for cron jobs. |
| `_hermes/Cron/` | Symlink → `~/.hermes/cron/` | Cron job output and config. |
| `Knowledge/Hermes/` | Reference notes | `_index.md` (overview), `Skills.md` (skill index), `Config.md` (config cheatsheet) |