# OB1 (Open Brain) vs. second_brain — Comparison & Integration Opportunities

Analyzed: 2026-04-02
Source repo: https://github.com/NateBJones-Projects/OB1
Priorities last revised: 2026-05-02 (after Karpathy Wiki vs. Open Brain video)

---

## Overview

| Dimension | second_brain (local) | OB1 / Open Brain |
|---|---|---|
| Nature | Personal, single-user, deeply integrated | Open-source community platform, extensible ecosystem |
| Size | ~35 files, fully self-contained | ~200+ files across server, docs, extensions, dashboards, integrations, recipes, skills |
| Maturity | Active personal project | v1.0 public release with CI/CD, PR review bots, Discord community |

---

## 1. Storage / Schema

**second_brain:** Fully normalized typed columns (`people[]`, `topics[]`, `category`, `status`) with GIN + HNSW indexes. Schema managed via Supabase CLI migrations.

**OB1:** Simple schema — `content`, `embedding`, `metadata` (JSONB blob). Flexible but less precise and slower to filter.

**Difference:** second_brain's typed columns support efficient queries like `people @> '{Mike}'`. OB1's JSONB approach is easier to extend without migrations but harder to query precisely.

---

## 2. Capture / Ingestion

**second_brain:** Supabase Edge Function runs OpenAI embeddings + Claude Haiku classification in parallel. Escalates to Claude Sonnet 4.6 if confidence < 0.7. Sets `needs_review` status on low confidence.

**OB1:** Capture handled inside the MCP server. Uses OpenRouter → gpt-4o-mini for metadata extraction. No confidence scoring, no escalation. Has deduplication via `upsert_thought` at capture time.

**Differences:**
- second_brain has a two-model cascade; OB1 uses a single cheaper model
- OB1 deduplicates at ingestion; second_brain does not (content fingerprint dedup in progress)
- OB1 routes through OpenRouter (one API key); second_brain requires OpenAI + Anthropic keys

---

## 3. MCP Server

**second_brain:** Local stdio process, 11 tools — `semantic_search`, `list_recent`, `capture_thought`, `get_stats`, `update_thought`, `archive_thought`, `delete_thought`, `get_thought`, `get_context`, `meeting_prep`, `get_needs_review`.

**OB1:** Remote HTTP endpoint (Hono + StreamableHTTP), 4 tools — `search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`. Requires `x-brain-key` auth header. Accessible from any AI client including Claude.ai in the browser.

**Differences:**
- second_brain is local-only; OB1 is remotely accessible from any device
- second_brain has far richer tooling (update, archive, delete, meeting prep, get_context, full raw text retrieval, needs_review queue)
- OB1 uses the newer StreamableHTTP MCP transport; second_brain uses stdio

---

## 4. Search

**second_brain:** Precise typed column filters. `get_context` combines semantic + keyword array matching. `meeting_prep` does combined semantic + per-person people-array lookups with deduplication and people-match prioritization. All searches respect `status` filter.

**OB1:** JSONB containment queries, configurable similarity threshold. No combined keyword+semantic. No meeting prep. No status filtering.

---

## 5. Digest System

**second_brain:** Fully built — 3 modes (daily, weekly, weekly-review). Delivery via Discord DM + Gmail (OAuth2). Nudge system checks capture recency and sends reflection prompts.

**OB1:** Documented as a recipe stub only — no implementation code.

---

## 6. Discord Bot

**second_brain:** Full working bot — capture, `!brain` queries, `!prep` meeting prep with `--people` flag. Runs as systemd service.

**OB1:** README instructions only, no bot code committed.

---

## 7. Dashboard

**second_brain:** Single static HTML file with Chart.js. Queries Supabase REST API directly.

**OB1:** Two full framework dashboards — SvelteKit and Next.js 15 — with auth, thought editing, duplicate management, audit view, dark theme.

---

## 8. Deployment

**second_brain:** Raspberry Pi 2 + systemd + `/etc/cron.d` (5 scheduled jobs). MCP server runs locally on dev machine.

**OB1:** Cloud-first — Supabase Edge Functions or Kubernetes self-hosted with direct PostgreSQL. Uses `pg_cron` for scheduling. No physical server required.

---

## 9. AI Models

**second_brain:** OpenAI (embeddings) + Anthropic Claude Haiku/Sonnet (classification, digests). Requires 2 API keys.

**OB1:** Everything routed through OpenRouter. 1 API key, model-agnostic. Configurable via env vars in Kubernetes variant.

---

## 10. Extensibility

**second_brain:** Monolithic personal repo, no plugin model.

**OB1:** 6 curated extensions (household, home maintenance, family calendar, meal planning, professional CRM, job hunt). Community import recipes (ChatGPT, Gmail, Obsidian, Google Takeout, Twitter, Instagram). Skill packs. Formal contribution pipeline.

---

## What second_brain Has That OB1 Doesn't

- Confidence-based escalation (Haiku → Sonnet cascade, `needs_review` status)
- Full thought retrieval by ID with raw text (`get_thought`)
- Field-level updates (`update_thought`)
- `meeting_prep` MCP tool with people-prioritized combined search
- `get_context` tool (topic-keyed keyword + semantic)
- `get_needs_review` tool surfacing low-confidence capture queue
- 3 digest modes with full implementation
- Nudge system for capture gaps
- Gmail delivery via OAuth2
- Working Discord bot with `!brain` and `!prep` commands
- Raspberry Pi deployment with systemd + cron
- Full status lifecycle (active → needs_review → archived) with filtering at all query layers

## What OB1 Has That second_brain Doesn't

- Remote HTTP MCP server (multi-client, browser-accessible)
- MCP access key authentication
- OpenRouter gateway (model-agnostic, single API key)
- Kubernetes self-hosted deployment option
- 6 structured domain extensions with compound cross-table awareness
- Community data import recipes (ChatGPT, Gmail, Obsidian, Twitter, Google Takeout, etc.)
- Two full-featured web dashboards (SvelteKit + Next.js 15)
- Content fingerprint deduplication at ingestion (in progress for second_brain)
- Configurable similarity threshold on search
- Row Level Security primitives for multi-user isolation
- Shared MCP server pattern for scoped access
- Skill packs (competitive analysis, financial model review, research synthesis, etc.)
- pg_cron-based scheduling (no server required)
- Knowledge graph layer (ob-graph: graph_nodes + graph_edges, recursive CTE traversal)
- Wiki compilation layer (wiki-compiler, wiki-synthesis, entity-wiki recipes)

---

## Integration Opportunities (Revised Priorities)

Priorities updated after Karpathy Wiki vs. Open Brain video (2026-04-29) which reframed
the value of contradiction detection and wiki/graph compilation.

### High Value / Relatively Easy
1. **Content fingerprint deduplication** ← IN PROGRESS (plan written, implementation pending)
   Hash raw text before insert to prevent duplicate thoughts. Plan: `plans/content_fingerprint_deduplication.md`
2. **Contradiction detection plugin** ← ELEVATED
   Surface contradictions at capture time before they accumulate silently. Most valuable gap
   identified from Karpathy video — wiki systems hide contradictions, database systems must
   actively surface them. OB1 does not yet have this; will need to build from scratch.
3. **Configurable similarity threshold**
   Expose as parameter on `semantic_search` instead of hardcoded value.
4. **OpenRouter as gateway**
   Single API key, model-agnostic, easier to swap models.

### Medium Value / More Work
5. **Remote HTTP MCP server** ← MOVED UP
   Hono + StreamableHTTP transport. Enables multi-client access (Claude.ai browser, second
   machine, future agents). Reinforced by local AI routing system concept — second_brain
   should be accessible from any surface. Pairs well with planned Python rewrite.
6. **Wiki/graph compilation layer** ← NEW
   Compile persistent topic pages from the database on demand. Reduces re-derivation tax
   each Claude session. ob-graph + wiki-compiler/wiki-synthesis recipes exist in OB1 as
   reference implementations. Hybrid architecture: database as source of truth, wiki as
   compiled readable view.
7. **Data import recipes**
   Migrate historical data from ChatGPT history, Gmail, Obsidian, Google Takeout.

### Lower Priority / Nice to Have
8. **Row Level Security + shared MCP**
   Scoped access for other users.
9. **pg_cron scheduling**
   Remove Raspberry Pi as single point of failure for digests and nudges.

### Deprioritized
- ~~Better dashboard~~ — wiki/graph compilation layer supersedes the standalone dashboard need.
  The wiki layer provides human-readable synthesis; a separate dashboard adds little on top of that.

---

## Backlog Stub — Proactive Resurfacing of External Insights in the Digest (surfaced 2026-07-02)

**The gap:** External/panned insights (`is_external = true`) are captured well but never *pushed* back. The digest deliberately keeps them out of the action slots (correct — they're reference, not to-dos; see `plans/done/personal_digest_fix.md`), so today they only faintly flavor "themes" and otherwise sit write-only. This is the "push" half of the second-brain that's currently missing: retrieval/synthesis is entirely **pull-based** (the user pulls insights when writing project plans), so blind spots they don't think to query stay invisible. Their own captured wisdom argues for fixing this: *passive KB < active loop*, *tap-on-shoulder surfacing*, *extract decision-relevant, don't hoard*.

**Proposed design — relevance-linked, NOT random.** Add one insight to the daily digest, tied to the day's work:

1. After the digest selects its Top 3 actions, run a `semantic_search` over those action titles/themes filtered to `is_external = true`.
2. Take the single best match and render it as:
   > 💡 **Bears on today:** *"<external insight>"* — surfaced because it relates to *<which action>*.

This closes the loop the whole system is missing: insight meets work at the point of need — automating, for one item a day, the just-in-time synthesis the user already does by hand when writing plans.

**Why relevance beats random:** a random daily insight reads as a horoscope — it becomes noise, trains the user to skim past the section, and is worse than nothing. A relevance-linked insight is a tap on the shoulder at the moment it can change a decision.

**Guardrails (keep it signal, avoid digest fatigue):**
- **One** insight, not a list.
- **Show the "why linked"** — the stated connection is what makes it feel intelligent rather than bolted-on.
- **Relevance floor** — if nothing clears ~60% against the day's actions, show *nothing*. Silence > filler.
- **Gate its appearance** — the section only renders when a real match exists, so low-relevance days keep the digest lean (protects the <150-word budget, which is already contested by Top 3 + the new `[BACKLOG]` line from `digest_backlog_filter.md`).
- Optional **weekly** "🎲 serendipity" pick (deliberately random) for cross-pollination — but keep it out of the *daily* and clearly label it as a bonus, not advice.

**Relationship to other items:**
- Finally gives the digest's `[EXTERNAL]` bucket an active job (complements the `[BACKLOG]` bucket in `digest_backlog_filter.md` — both are digest-surface changes and should be designed together).
- Adjacent to `get_gaps` (`mcp_improvements.md §1`): that pushes *what's missing*; this pushes *what's relevant and already captured*.

**Status:** stub — captured 2026-07-02, relevance-linked design agreed, implementation deferred. Independently confirmed 2026-07-02 by a `/recap` grading session on another machine (thought `11c17aed`): retrieval/synthesis graded B+ (user reliably pulls from the brain when planning — that part works), but "synthesis is entirely PULL-based — blind spots the user doesn't think to query stay invisible" was the one thing keeping the overall grade at A- instead of A. This stub is the fix for that specific gap. **Needs a real planning session before implementation** — this sketch is directional, not a build spec. See `recall_before_work_skill.md` for a related-but-distinct idea (automatic pull at session start) that does NOT substitute for this fix — that skill automates what the user already does well; this stub fixes what they can't do at all (query for something they don't know to ask about).

