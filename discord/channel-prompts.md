# Discord Channel Configuration

Hermes Agent integrates with Discord via the Gateway. Each channel has specific behavior configured through channel prompts.

## Channel Map

| Channel | Type | Auto-Reply | Purpose |
|---------|------|------------|---------|
| `#hermes-chat` | Free-response | ✅ Yes | Main ops channel — everything auto-replies |
| `#hermes-knowledge` | Free-response | ✅ Yes | Post content → auto-extracted to vault |
| `#announcements` | Read-only | ❌ No | Cron job outputs, daily summaries, wiki updates |
| `#sys-status` | Read-only | ❌ No | System health reports, uptime, service status |
| `#logbook` | Read-only | ❌ No | Vault change detection logs |
| `#general` | @mention only | ❌ Only when pinged | General conversation |
| `#admin` | @mention only | ❌ Only when pinged | Config, status checks, slash commands |
| `#wiki-ingest` | Read-only | ❌ No | Wiki activity logs (cron output) |
| `#dev` | Free-response | ✅ Yes | Technical discussion, code questions |

## Free-Response Channels (Auto-Reply Without @Mention)

### 🧠 Hermes Knowledge (`#hermes-knowledge`)
When someone posts content (URLs, text, files, video links):
1. ANALYZE everything — read URLs, transcribe YouTube links, read attached files, extract text from PDFs, examine code snippets
2. Get IN-DEPTH knowledge — extract key concepts, insights, techniques, actionable information
3. DETERMINE the right vault destination:
   - Educational content / tutorials → `Knowledge/<topic>/` with `[[wikilinks]]`
   - Code snippets / CLI commands → `Knowledge/Cheat Sheets/`
   - Setup instructions / config → `Knowledge/Hermes/` or relevant topic
   - Project ideas/seeds → `Jornal/Ideas/`
   - Active project updates → `Projects/`
   - Career/job stuff → `Jornal/Career/`
   - Infrastructure/homelab → `Kakurega Sector/`
   - Wiki-worthy topics → `Wiki/` (create/update entity or concept page)
   - Research / reference → `Knowledge/` as standalone note
   - Time-based captures → `Jornal/Daily/YYYY-MM-DD.md`
4. Always read existing notes first — NO duplicates
5. Notes must be EVERGREEN — no "today", "yesterday", "in this article" references
6. Use `[[wikilinks]]` to connect to related vault notes
7. Save raw copy to `00-Inbox/` for archival
8. Post summary of what was extracted, created, and where it was filed

### 🤖 Hermes Chat (`#hermes-chat`)
Free-response ops channel. Respond to ALL messages here automatically without requiring @mention.

### 💻 Dev (`#dev`)
Technical discussion channel. Focus on code, commands, and architecture. Be concise.

## Key Discord Config Settings

```yaml
discord:
  require_mention: true              # Need @Hermes in non-free-response channels
  auto_thread: true                   # Every message spawns a thread
  thread_require_mention: false       # Free to chat in threads
  history_backfill: true              # Load recent history on connect
  history_backfill_limit: 50          # Last 50 messages
  reactions: true                     # Auto-react to acknowledge messages
```
