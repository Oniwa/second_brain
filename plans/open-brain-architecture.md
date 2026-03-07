# Open Brain: Architecture Overview

## Vision

A database-backed, AI-accessible knowledge system you own outright — no SaaS middlemen. One brain that every AI tool you use (Claude, ChatGPT, Cursor, Claude Code) can plug into via MCP. You capture a thought from anywhere, and seconds later it's embedded, classified, and searchable by meaning from any AI tool or agent.

**Target cost:** ~$0.10–0.30/month on Supabase free tier + minimal API calls.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CAPTURE POINTS                         │
│                                                             │
│  Discord/Slack    Claude/ChatGPT    CLI Tool    Zapier/n8n  │
│  (bot channel)    (via MCP write)   (curl/py)  (webhooks)   │
└──────────┬──────────────┬──────────────┬──────────────┬─────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER                          │
│                  Supabase Edge Functions                     │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  Embedding   │  │  Metadata    │  │   Classification   │ │
│  │  Generation  │  │  Extraction  │  │   & Routing        │ │
│  │  (OpenAI     │  │  (Haiku →    │  │   (Haiku first,    │ │
│  │   small)     │  │   Sonnet)    │  │    Sonnet if <0.7) │ │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘ │
│         │                │                     │            │
│         ▼                ▼                     ▼            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              PARALLEL STORAGE WRITES                    ││
│  └─────────────────────────────────────────────────────────┘│
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                            │
│               Supabase (Postgres + pgvector)                │
│                                                             │
│  ┌──────────────────────────────────────────────────┐       │
│  │  thoughts                                        │       │
│  │  ├── id (uuid)                                   │       │
│  │  ├── raw_text (text)                             │       │
│  │  ├── embedding (vector 1536)                     │       │
│  │  ├── category (person|project|idea|admin|insight)│       │
│  │  ├── title (text)                                │       │
│  │  ├── summary (text)                              │       │
│  │  ├── people (text[])                             │       │
│  │  ├── topics (text[])                             │       │
│  │  ├── action_items (text[])                       │       │
│  │  ├── confidence (float)                          │       │
│  │  ├── source (text)                               │       │
│  │  ├── created_at (timestamptz)                    │       │
│  │  └── updated_at (timestamptz)                    │       │
│  └──────────────────────────────────────────────────┘       │
│                                                             │
│  pgvector index for semantic search                         │
│  GIN indexes on people[], topics[], category                │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RETRIEVAL LAYER                          │
│              MCP Server (local-first)                       │
│                                                             │
│  Tools exposed:                                             │
│  ├── semantic_search(query, limit) — find by meaning        │
│  ├── list_recent(days, category) — browse recent captures   │
│  ├── capture_thought(text, source) — write from any client  │
│  ├── get_stats() — thinking patterns over time              │
│  └── get_context(topic) — pull all context on a topic       │
│                                                             │
│  Connects to:                                               │
│  Claude Desktop, Claude Code, Cursor, VS Code, ChatGPT,    │
│  any MCP-compatible client                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Details

### 1. Storage Layer — Supabase Postgres + pgvector

The foundation. A single `thoughts` table with vector embeddings for semantic search.

**Why Supabase:**
- Free tier includes Postgres with pgvector extension
- Built-in Edge Functions for processing logic
- Row-Level Security for access control
- Solid REST and client APIs
- Boring, battle-tested technology underneath

**Core Table: `thoughts`**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | uuid (PK) | Unique identifier, auto-generated |
| `raw_text` | text | Exact text you captured — never modified |
| `embedding` | vector(1536) | OpenAI text-embedding-3-small output |
| `category` | text | person, project, idea, admin, insight |
| `title` | text | AI-generated short title |
| `summary` | text | AI-generated one-liner |
| `people` | text[] | Names of people mentioned |
| `topics` | text[] | Topic tags extracted by AI |
| `action_items` | text[] | Specific next actions extracted |
| `confidence` | float | AI classification confidence (0–1) |
| `source` | text | Where it was captured (discord, slack, mcp, cli) |
| `status` | text | active, needs_review, archived |
| `created_at` | timestamptz | When captured |
| `updated_at` | timestamptz | Last modified |

**Indexes:**
- **HNSW index** on `embedding` column for fast semantic search
- **GIN index** on `people`, `topics` arrays for filtered queries
- **B-tree index** on `category`, `created_at`, `status`

**Key design decisions:**
- Single table, not four separate databases — simpler to query, embed, and search across
- Category as a column rather than separate tables — vector search works across all thoughts regardless of type
- Raw text always preserved — you can always re-process if the AI extraction improves
- Confidence score stored — low-confidence entries get flagged for review (the "bouncer" pattern)

**Embedding model: `text-embedding-3-small` (1536 dimensions)**
Starting with the small model — it's cheap, fast, and more than sufficient for a personal knowledge base. The raw text is always preserved, so upgrading to `text-embedding-3-large` (3072 dimensions) later is a straightforward batch job: query all rows, call the new embedding API, update the vectors, and rebuild the HNSW index. With a few thousand thoughts, this runs in minutes and costs pennies. The schema change is just altering the vector column dimension. Start small, upgrade only if semantic search is missing connections it shouldn't.

### 2. Processing Layer — Supabase Edge Functions

Two Edge Functions handle the intelligence work:

**`process-thought` (triggered on capture):**
1. Receives raw text + source identifier
2. Calls OpenAI embedding API (`text-embedding-3-small`, 1536 dimensions) → generates vector
3. Calls **Claude Haiku** with classification prompt → returns structured JSON
4. Checks confidence score — if below 0.7, **re-runs classification with Claude Sonnet** for a second opinion
5. Writes everything to the `thoughts` table in parallel
6. Returns confirmation with title, category, confidence

**Tiered classification logic:**
Most captures are straightforward ("Talked to Sarah about the relaunch deadline") and Haiku handles them at high confidence for minimal cost. Ambiguous or complex inputs ("that thing Mike mentioned about the Q3 pivot might connect to the pricing discussion") will score below the 0.7 threshold and get escalated to Sonnet for richer metadata extraction. Expected result: Haiku handles ~90% of captures, keeping per-thought cost low while Sonnet provides deeper reasoning only when it matters.

```
Raw text → Haiku classification → confidence ≥ 0.7? → Store
                                  confidence < 0.7? → Sonnet re-classification → Store
```

**`generate-digest` (triggered on schedule or on-demand):**
1. Queries active projects, recent captures, pending action items
2. Sends context to Claude with a summarization prompt
3. Returns a digest: top 3 actions, one stuck item, one pattern noticed

**Classification prompt contract (JSON schema):**
```json
{
  "category": "person|project|idea|admin|insight",
  "title": "Short descriptive title",
  "summary": "One sentence summary",
  "people": ["Name1", "Name2"],
  "topics": ["topic1", "topic2"],
  "action_items": ["Specific next action"],
  "confidence": 0.85
}
```

The prompt is treated like an API — fixed input format, fixed output format, no creative latitude. This is Nate's Principle 3 (treat prompts like APIs, not creative writing). The same prompt contract is used for both Haiku and Sonnet — only the model changes, not the interface.

### 3. Capture Points — Multiple Inputs, One Pipeline

All capture points funnel into the same `process-thought` Edge Function.

| Capture Point | How It Works | Best For |
|---------------|-------------|----------|
| **Discord channel** | Bot watches private `#sb-inbox` channel → calls Edge Function → replies in-thread with receipt. Free, no message history limits, no integration caps | Quick thoughts anytime, mobile capture, always-on log |
| **Slack channel** | Zapier/n8n watches channel → calls Edge Function. Plug-and-play with Zapier triggers, but free tier has 90-day history limit and 10-integration cap | Teams already on Slack for work |
| **MCP `capture_thought` tool** | Any MCP client writes directly to Supabase | Capturing while chatting with AI |
| **CLI tool** | Simple curl/Python script hitting Edge Function | Terminal-first workflow |
| **Zapier/n8n webhook** | Generic HTTP endpoint → Edge Function | Email forwarding, calendar events |
| **Voice (future)** | Whisper API → text → Edge Function | Hands-free capture |

**The core principle:** Capture must be frictionless. One action, zero decisions. The system does the classifying, routing, and organizing.

### 4. Retrieval Layer — MCP Server

The MCP server is what makes this agent-readable. It exposes your brain to any MCP-compatible client.

**Tools:**

| Tool | Input | Output | Use Case |
|------|-------|--------|----------|
| `semantic_search` | query string, optional limit & category filter | Ranked thoughts with similarity scores | "What was I thinking about career changes?" |
| `list_recent` | days (default 7), optional category | Chronological recent captures | "What did I capture this week?" |
| `capture_thought` | text, source | Confirmation with extracted metadata | Writing to brain from any AI client |
| `get_stats` | optional time range | Category distribution, capture frequency, top topics | "How am I using my brain?" |
| `get_context` | topic string | All thoughts related to a topic, clustered | "Give me everything about Project X" |

**MCP server hosting:** Local-first. Run as a local Node.js or Python process on each machine (home + office). Connects to Supabase via client library — the server is a thin query layer, so running it on multiple machines just means keeping the same code synced. If multi-machine access becomes friction, upgrade path is to expose MCP tools as Supabase Edge Functions with HTTP transport (no extra hosting cost).

---

## Build Phases

### Phase 1: Foundation (The Core Loop)
- Set up Supabase project with pgvector
- Create `thoughts` table with schema and indexes
- Build `process-thought` Edge Function
- Test with direct API calls (curl)
- **Milestone:** You can capture a thought via API and it gets embedded + classified

### Phase 2: MCP Server
- Build MCP server with `semantic_search`, `list_recent`, `capture_thought`
- Connect to Claude Desktop or Claude Code
- Test semantic retrieval
- **Milestone:** You can search your brain from Claude and capture thoughts from any MCP client

### Phase 3: Capture Points
- Set up Discord server + bot (or Slack channel + Zapier/n8n)
- Build CLI capture script
- Add confirmation replies (the "receipt" pattern)
- **Milestone:** Multiple frictionless capture points all feeding the same brain

### Phase 4: Surfacing & Digests
- Build `generate-digest` Edge Function (Claude Sonnet summarizes recent thoughts)
- Deliver digest via **both Discord DM and email**
- Digest format: top 3 actions, one stuck item, one pattern noticed
- Schedule: TBD (daily, weekly, or both)
- Build `discord/digest.py` — calls Edge Function, sends Discord DM + email
- **Milestone:** The system proactively tells you what matters today

### Phase 5: Enhancements
- Memory migration (pull from Claude memory, ChatGPT memory)
- Dashboard for thinking patterns
- Meeting prep automation
- Birthday/follow-up reminders
- Weekly review synthesis

---

## Engineering Principles Applied

These map to Nate's principles from the transcripts, adapted for this architecture:

| # | Principle | How It Shows Up |
|---|-----------|----------------|
| 1 | One reliable human behavior | Capture a thought — that's it. Everything else is automated |
| 2 | Separate memory / compute / interface | Postgres = memory, Edge Functions = compute, MCP + Discord/Slack = interface |
| 3 | Prompts as APIs | Classification prompt returns strict JSON, no creative latitude |
| 4 | Trust mechanism, not just capability | Inbox log, confidence scores, fix-in-thread corrections |
| 5 | Safe defaults when uncertain | Low confidence → escalate to Sonnet; still low → status: needs_review, not auto-filed |
| 6 | Small, frequent, actionable output | Daily digest under 150 words, weekly under 250 |
| 7 | Next action as unit of execution | action_items field extracts specific executable steps |
| 8 | Routing over organizing | AI classifies into stable categories — you never organize |
| 9 | Minimal fields | Single table, ~12 columns. Add complexity only when evidence demands |
| 10 | Design for restart | Miss a week? Just capture a brain dump and resume |
| 11 | Core loop first, modules later | Phase 1–2 = core loop. Phase 3–5 = modules |
| 12 | Maintainability over cleverness | Supabase managed infra, simple Edge Functions, clear logs |

---

## What Makes This Different From V1 (Notion-Based)

| Aspect | V1 (Notion) | V2 (Open Brain) |
|--------|-------------|-----------------|
| Storage | Notion databases (4 separate) | Postgres + pgvector (1 table) |
| Search | Keyword / filter based | Semantic (meaning-based) |
| Agent readable | No — designed for human eyes | Yes — MCP protocol native |
| Lock-in | Notion API dependency | Open-source Postgres you own |
| Cross-tool | Only through Zapier pipes | Any MCP client reads/writes directly |
| Cost | Notion plan + Zapier plan | ~$0.10–0.30/month |
| Embeddings | None | Every thought vectorized |
| Portability | Export to CSV/Markdown | Standard Postgres dump/restore |

---

## Decisions Made

| # | Decision | Choice | Upgrade Path |
|---|----------|--------|-------------|
| 1 | Embedding model | OpenAI `text-embedding-3-small` (1536 dims) | Batch re-embed to `text-embedding-3-large` (3072 dims) if semantic search quality needs improvement. Raw text preserved, so re-processing is always possible. |
| 2 | Classification LLM | Tiered: Haiku first, Sonnet on escalation | Haiku handles ~90% of captures. If confidence < 0.7, automatically re-classifies with Sonnet. Same prompt contract for both — only the model changes. |
| 3 | MCP server hosting | Local-first (Node.js/Python on each machine) | If multi-machine friction arises, move to Supabase Edge Functions as remote HTTP MCP endpoint — no extra hosting cost. |

## Decisions Closed

1. **Digest delivery:** Discord DM — bot sends a DM on the existing Discord setup.
2. **Migration:** Yes — import existing Claude + ChatGPT memory exports on initial setup (Phase 5 tooling).

---

## Status

### Phase 1 — ✅ Complete
Files:
- `supabase/migrations/001_init.sql` — thoughts table, HNSW + GIN indexes, `semantic_search()` SQL function
- `supabase/functions/process-thought/index.ts` — embedding + tiered Haiku/Sonnet classification
- `supabase/config.toml` — project config
- `.env.example` — required secrets
- `scripts/test_capture.sh` — curl smoke test

Milestone achieved: thoughts captured via API are embedded + classified and stored in Supabase.

---

### Phase 2 — ✅ Complete: MCP Server
Files:
- `mcp/src/server.ts` — MCP server with 6 tools
- `mcp/package.json` — Node.js dependencies
- `mcp/tsconfig.json` — TypeScript config

**Tools implemented:**
| Tool | What it does |
|------|-------------|
| `semantic_search(query, limit?, category?)` | Embeds query → calls `semantic_search()` RPC → returns ranked thoughts |
| `list_recent(days?, category?)` | Queries thoughts table by date, returns chronological list |
| `capture_thought(text, source?)` | Calls `process-thought` Edge Function → full pipeline |
| `get_stats(days?)` | Category breakdown + top topics over time |
| `get_context(topic)` | Semantic search + keyword match on topics[], merged & deduplicated |
| `delete_thought(id)` | Permanently removes a thought by UUID |

Wired to Claude Code via `claude mcp add`. Milestone achieved: brain is searchable and writable from Claude.

---

### Phase 3 — In Progress: Capture Points

#### CLI Tool — ✅ Complete
File: `scripts/brain.py` — cross-platform (Windows + Linux), zero dependencies beyond stdlib.
```
python brain.py "thought"               # capture
python brain.py --recent [--days N]     # list recent
python brain.py --search "query"        # semantic search
python brain.py --stats [--days N]      # usage stats
```
Linux alias: add `alias brain="python3 /path/to/scripts/brain.py"` to `~/.bashrc`

---

#### Discord Bot — In Progress

**One-time Discord setup (do this first):**

1. **Create a Discord account** at discord.com (or log in)
2. **Create your server** — click **+** in the left sidebar → "Create My Own" → "For me and my friends" → name it "Second Brain"
3. **Create the bot at the Developer Portal**
   - Go to discord.com/developers/applications
   - Click **New Application** → name it "Second Brain Bot"
   - Go to **Bot** → click **Add Bot**
   - Under **Token** → click **Reset Token** → copy it (this is `DISCORD_BOT_TOKEN`)
   - Scroll down → **Privileged Gateway Intents** → enable **Message Content Intent**
4. **Invite the bot to your server**
   - Go to **OAuth2 → URL Generator**
   - Scopes: check **bot**
   - Bot Permissions: check **Read Messages/View Channels**, **Send Messages**, **Create Public Threads**, **Send Messages in Threads**
   - Copy the generated URL → open in browser → invite bot to your Second Brain server
5. **Create the `#sb-inbox` channel** in your server

**Files to create:**
- `discord/bot.py` — Discord bot (Python)
- `discord/requirements.txt` — dependencies (`discord.py`)

**Phase 3 milestone:** Multiple frictionless capture points all feeding the same brain — no dependency on Claude Code being open.
