# Discord Channel Configuration

Hermes Agent integrates with Discord via the Gateway. Each channel has specific behavior configured through channel prompts.

## Channel Map

| Channel | Type | Auto-Reply | Purpose |
|---------|------|------------|---------|
| `#hermes-chat` | Free-response | ✅ Yes | Main ops channel — everything auto-replies |
| `#announcements` | Read-only | ❌ No | Cron job outputs, daily summaries, wiki updates |
| `#sys-status` | Read-only | ❌ No | System health reports, uptime, service status |
| `#logbook` | Read-only | ❌ No | Vault change detection logs |
| `#general` | @mention only | ❌ Only when pinged | General conversation |
| `#admin` | @mention only | ❌ Only when pinged | Config, status checks, slash commands |
| `#wiki-ingest` | Free-response | ✅ Yes | Post content → auto-extracted to Wiki |
| `#inbox` | Free-response | ✅ Yes | Post content → auto-filed to vault |
| `#dev` | Free-response | ✅ Yes | Technical discussion, code questions |

## Channel Prompt Details

### 🧠 Wiki Ingest (`#wiki-ingest`)
When someone posts content (URLs, text, files, video links):
1. Analyze everything — read URLs, transcribe YouTube links, read attached files
2. Extract deep knowledge — understand concepts, connect ideas
3. Route output:
   - Wiki-worthy → create/update entity/concept pages in `/Wiki/`
   - Knowledge guides → `/Knowledge/` with `[[wikilinks]]`
   - Project-related → `/Projects/`
4. Always use `[[wikilinks]]` to connect to existing notes
5. Save raw copy to `00-Inbox/` as timestamped markdown

### 📥 Inbox (`#inbox`)
When someone posts content:
1. Analyze everything — read URLs, transcribe video, read attached files
2. Determine the right vault destination:
   - Knowledge/guides → `/Knowledge/`
   - Project ideas → `/Jornal/Ideas/`
   - Infrastructure → `/Kakurega Sector/`
   - Wiki-worthy → `/Wiki/`
   - Time-based → `/Jornal/Daily/YYYY-MM-DD.md`
   - General → `/Knowledge/General/`
3. Create well-structured note with proper headings and links
4. Save raw copy to `00-Inbox/`

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