# Vault Structure & AGENTS.md Rules

This documents the Obsidian vault's folder architecture and processing rules that Hermes Agent follows.

## Folder Roles

| Folder | Role | Agent Behavior |
|--------|------|----------------|
| `00-Inbox/` | Raw captures from Discord/WhatsApp/CLI | Default write target for new captures. Prompt user to process items older than 7 days. |
| `Knowledge/` | Evergreen reference | File extracted knowledge here. Create new notes, update existing ones, link related topics. |
| `Projects/` | Active projects | Each subfolder is a project. Respect existing project notes. Create/update project-tracker notes. |
| `Kakurega Sector/` | Infrastructure & homelab | Ongoing setup docs, machine specs, network configs. Read-only reference — do not reorganize. |
| `Jornal/` | Timeline / daily capture | Append-only. Do not rearrange existing notes. |
| `Jornal/Daily/` | Personal daily scratchpad | User writes manually. Agent processes nightly: extract knowledge, update projects, convert TODOs. |
| `Jornal/Ideas/` | Project seeds | Read for context when brainstorming. File new ideas here. |
| `Jornal/Prompts/` | Prompt engineering notes | Reference for prompt patterns. |
| `Jornal/Career/` | Job search & career | Read for context. Do not share outside vault. |
| `Jornal/ToDo.md` | Auto-maintained task list | Rebuilt nightly with open tasks from all notes. Do not edit manually. |
| `Wiki/` | LLM Wiki (Karpathy pattern) | Persistent compounding knowledge base. Entities, concepts, comparisons, queries. |
| `Private/` | Sensitive data | **Never expose** to external APIs, web search, or Discord/WhatsApp responses. |
| `Template/` | Note templates | Use when creating new notes of a given type. |
| `_hermes/` | Hermes bridge | Skills, scripts, memory, cron symlink. Syncs between agent and vault. |

## Processing Pipeline

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ Discord  │───→│ 00-Inbox/    │───→│ Knowledge/   │
│ WhatsApp │    │ (raw capture) │    │ Projects/    │
│ CLI      │    │              │    │ Wiki/        │
└──────────┘    └──────┬───────┘    └──────────────┘
                       │
                ┌──────▼───────┐
                │ 7d → Archive │
                │ 30d → Purge  │
                └──────────────┘

┌──────────────┐    ┌──────────────┐
│ Nightly      │───→│ Knowledge    │
│ Processor    │    │ extraction   │
│ (22:00)      │    │ Wiki updates │
└──────────────┘    └──────────────┘

┌──────────────┐    ┌──────────────┐
│ Nightly Task  │───→│ ToDo.md      │
│ Processor    │    │ (auto-rebuild)│
│ (23:00)      │    │              │
└──────────────┘    └──────────────┘

┌──────────────┐    ┌──────────────┐
│ Wiki Ingest  │───→│ Entity pages │
│ (03:00)      │    │ Concept pages│
│              │    │ Raw archive  │
└──────────────┘    └──────────────┘
```

## Nightly Cron Jobs

### User Daily Note Processor (22:00)
1. Read today's user daily note from `Jornal/Daily/YYYY-MM-DD.md`
2. Extract:
   - Code snippets → `Knowledge/Cheat Sheets/`
   - Learning/knowledge → `Knowledge/` with `[[wikilinks]]`
   - Project tasks → update relevant `Projects/` note
   - Ideas → `Jornal/Ideas/` if concept, `Projects/` if actionable
3. Cross-reference with existing notes
4. Update `Wiki/` topic summaries if content adds new knowledge

### Task Processor (23:00)
1. Scan all notes for `- [ ]` (open) and `- [x]` (done) items
2. Rebuild `Jornal/ToDo.md` with open tasks grouped by source folder
3. Flag tasks untouched for 7+ days

### Wiki Ingest (03:00)
1. Run `vault-wiki-diff.py` to detect new/changed files
2. For each new file: read content, check existing wiki, create/update pages
3. Save raw copies to `Wiki/raw/articles/`
4. Update `Wiki/index.md` and `Wiki/log.md`

## Key Design Principles

- **Automated cleanup**: Old inbox items auto-archive (7d) and purge (30d)
- **Never lose context**: Session exports every 30m, all conversations persisted
- **Wiki as compounding knowledge**: Each ingest builds on previous entries, creating a connected knowledge graph
- **Privacy first**: `Private/` is never exposed to any external service
- **Hermes bridge**: `_hermes/` directory syncs skills, memory, and scripts between Obsidian and the agent