# Second Brain — Claude Onboarding

Read this before starting work on a new machine or in a new session.
Full architecture and phase details are in `plans/open-brain-architecture.md`.

---

## Project Summary
A personal knowledge system backed by Supabase (Postgres + pgvector). Thoughts are captured
from multiple sources, embedded by OpenAI, classified by Claude Haiku/Sonnet, and stored.
Retrieval is via MCP tools, CLI, or Discord. Daily/weekly digests delivered via Discord DM + Gmail.

**Repo:** https://github.com/Oniwa/second_brain
**Active branch:** `develop` (merge to `main` when stable)

---

## Language Rules
- New scripts → **Python** only
- MCP server → Node.js/TypeScript (already built, do not rewrite)
- Edge Functions → Deno/TypeScript (Supabase requirement, do not rewrite)

---

## Infrastructure
- **Supabase project ref:** `zkdblldjdgadqukpttwl`
- **Supabase Edge Functions deployed:** `process-thought`, `generate-digest`
- **MCP server:** registered in Claude Code via `claude mcp add second-brain`
  - Run with: `cd mcp && npm start`
- **Discord bot:** `discord/bot.py` — must be running to capture from Discord
- **Digest:** `discord/digest.py --daily` / `--weekly`

---

## Key Files
| File | Purpose |
|------|---------|
| `supabase/migrations/001_init.sql` | Schema, indexes, `semantic_search()` SQL function |
| `supabase/functions/process-thought/index.ts` | Embedding + Haiku/Sonnet classification |
| `supabase/functions/generate-digest/index.ts` | Daily/weekly digest generation via Sonnet |
| `mcp/src/server.ts` | MCP server (6 tools) |
| `scripts/brain.py` | CLI capture tool (cross-platform) |
| `discord/bot.py` | Discord bot — watches `#sb-inbox` |
| `discord/digest.py` | Digest delivery — Discord DM + Gmail |
| `discord/second-brain-bot.service` | systemd service for Pi hosting |
| `scripts/setup_rpi.py` | One-shot Raspberry Pi setup script |
| `.env.example` | All required environment variables |
| `plans/open-brain-architecture.md` | Full architecture, decisions, phase status |

---

## Required .env Variables
```
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
DISCORD_BOT_TOKEN
DISCORD_USER_ID
GMAIL_RECIPIENT
```
Also needed in project root (gitignored): `credentials.json`, `token.json` (Gmail OAuth)

---

## Phase Status
| Phase | Status | Summary |
|-------|--------|---------|
| 1 — Foundation | ✅ | Supabase schema + `process-thought` Edge Function |
| 2 — MCP Server | ✅ | 6 tools: semantic_search, list_recent, capture_thought, get_stats, get_context, delete_thought |
| 3 — Capture Points | ✅ | CLI (`brain.py`), Discord bot, MCP |
| 4 — Digests | ✅ | Daily + weekly via Discord DM + Gmail. Cron jobs pending Pi day. |
| 5 — Enhancements | 🔜 | Memory migration, nudge system, dashboard, meeting prep |

---

## Raspberry Pi Hosting (pending)
The Pi will run the Discord bot (systemd) and digest cron jobs.
All setup is automated — see `plans/open-brain-architecture.md` → Pi day section.
Run `sudo python3 scripts/setup_rpi.py` on the Pi after cloning and copying `.env`.

---

## Key Decisions
- Digest delivery: **Discord DM + Gmail** (both, every run)
- Memory migration: **Yes** — import Claude + ChatGPT exports on Phase 5
- Embedding: `text-embedding-3-small` (1536 dims, OpenAI)
- Classification: Haiku first → Sonnet if confidence < 0.7
- Completed thoughts: **archive them** (`status=archived`) — preserved for history/patterns but invisible to searches and digests

---

## How to Get Up to Speed Fast
1. Read this file ✓
2. Read `plans/open-brain-architecture.md` for full detail on any phase
3. Check `git log --oneline -20` to see recent changes
4. Ask the user what they want to work on next
