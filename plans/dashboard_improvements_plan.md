# Dashboard Improvements Plan

Analyzed: 2026-05-04

---

## Current State

`dashboard/index.html` — single static HTML file, no framework, dark theme, Chart.js. Local-only, read-only, anon key.

**What we have:**
- Stat cards: Total, Active, Needs Review, Archived, Last 30 days, People tracked
- Charts: Daily captures (30 days), Category breakdown, Status breakdown, Capture source, Top 10 topics

---

## OB1 Dashboard Comparison

OB1 has two full framework dashboards: SvelteKit (`open-brain-dashboard`) and Next.js 15 (`open-brain-dashboard-next`). Neither is worth adopting — both require build pipelines and auth. Our static HTML approach is correct for a local-only dashboard.

**OB1 Next.js routes assessed:**

| Route | What it does | Our verdict |
|---|---|---|
| `/audit` | Paginated list, bulk select + delete | Adapt as Task Audit tab (archive with reason instead of delete) |
| `/duplicates` | Semantic near-duplicate detection, configurable threshold | Deferred — depends on semantic dedup feature that doesn't exist yet |
| `/kanban` | Tasks/ideas workflow board | Not planned — adds complexity |
| `/search` | Full thought search with type/topic/person filters | Remote HTTP MCP server is the right fix for multi-client access |
| `/thoughts/[id]` | Thought detail + edit in browser | Covered by inline edit in Task Audit tab |

---

## What We're Taking From OB1

### 1. Task Audit Tab (adapted from OB1 `/audit`) ← NEXT UP
Show active thoughts with non-empty `action_items[]`, oldest first. Per-row archive button + optional reason field. Reason appended to `raw_text` as `[Archived: reason]`. Inline `raw_text` edit included (see Edit Feature below). Uses service role key — acceptable for local-only dashboard.

### 2. Wiki Pages Tab (our own implementation)
Table: slug / title / thought_count / last_compiled_at / stale flag. Click to expand full markdown content. Reads from `wiki_pages` table via Supabase REST API.

### 3. Top 10 People Chart
Horizontal bar chart alongside existing Top 10 Topics chart. Count of thoughts per person from `people[]` arrays — data already fetched in `fetchAll()`.

### Not Adopted from OB1
- Framework rewrite — static HTML is correct for local-only use
- Auth — unnecessary for local-only dashboard
- Kanban — not planned
- Near-duplicate UI — deferred, depends on semantic dedup feature
- Full thought search UI — Remote HTTP MCP server solves multi-client access more completely

---

## Edit Feature (raw_text, both surfaces)

### Design Decisions
- **Edit scope:** `raw_text` only on both Discord and browser
- **Resynthesis:** Yes — after raw_text update, re-embed + re-classify via Edge Function. Stale embedding defeats semantic search; cost equals a fresh capture; edits are rare.
- **Status on resynthesize:** Preserve existing status always — never overridden by resynthesis. Status is a human decision.
- **Implementation:** Extend `process-thought` Edge Function to accept optional `id` param. If present, patch existing row instead of insert. All edit surfaces route through this same path.
- **Content hash:** Updated as part of resynthesis flow (per content_fingerprint_deduplication.md plan).

### Discord
- Command: `!update {id} {new text}` — replaces raw_text, triggers resynthesis
- Response: confirmation with new title + category

### Browser (Task Audit tab)
- Inline edit field for raw_text on each thought row
- Submit → calls Edge Function update mode → refreshes row with updated title/summary/topics

### Files to Change

| File | Change |
|---|---|
| `supabase/functions/process-thought/index.ts` | Accept optional `id` param; patch existing row when present; preserve status |
| `mcp/src/server.ts` | `updateThought()` routes through Edge Function when raw_text changes |
| `discord/bot.py` | Add `!update {id} {new text}` handler |
| `dashboard/index.html` | Task Audit tab with inline edit + archive |

---

## Implementation Roadmap

### Phase 1 — Task Audit Tab (next up)
1. Add service role key to dashboard for write operations
2. Tab: active thoughts with non-empty `action_items[]`, oldest first
3. Per-row archive button + reason field (PATCH Supabase REST directly)

### Phase 2 — Edit Feature
4. Extend `process-thought` Edge Function for update mode (optional `id` param)
5. Update MCP `updateThought()` to route through Edge Function for raw_text changes
6. Add Discord `!update {id} {new text}` handler in `discord/bot.py`
7. Add inline raw_text edit to Task Audit tab rows

### Phase 3 — Additional Charts & Tabs
8. Top 10 People horizontal bar chart (data already available in `fetchAll()`)
9. Wiki Pages tab (reads `wiki_pages` table)

### Deferred
- Near-duplicate management UI (depends on semantic dedup feature not yet built)
