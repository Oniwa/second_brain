# Current Work

## Active
**Wiki item 2 — Source labels (is_external field)**

Add `is_external BOOLEAN DEFAULT false` to thoughts schema so the wiki compiler can label YouTube-sourced insights with `[Source: ...]` correctly.

Steps (in order):
1. `supabase/migrations/005_is_external.sql` — add column + backfill (`is_external = true` where `raw_text ILIKE '%Source:%'`)
2. `supabase/functions/process-thought/index.ts` — accept and store `is_external` from capture payload
3. `mcp/src/server.ts` — pass `is_external` flag through `capture_thought`
4. Pan skill — pass `is_external=true` on every capture + include YouTube URL in raw text
5. Recompile affected wiki pages

Backfill rule locked in: `6fcc453`
Spec: `plans/wiki_implementation.md` → Follow-up 1 — Source Labels

---

## Up Next
- **Wiki item 3** — Project pages (spec grouping mechanism first — sample project thoughts to decide: topics[] reuse vs. `project_name` field vs. title prefix)
- **Wiki item 1** — Decide cron location (Pi vs PC vs on-demand) — blocks stale detection cron
- **Dashboard item 11** — Inline `raw_text` edit in `audit.html` (backend is live, this is UI only)

---

## Recently Shipped
| Date | Item | What |
|---|---|---|
| 2026-05-05 | Dashboard 8-10 | Edge Function update mode (`id` param), MCP `updateThought` re-routes through Edge Function, Discord `!update` command |
| 2026-05-04 | Wiki MVP | `compile_wiki.py`, `wiki_pages` table, MCP `get_wiki_page` + `list_wiki_pages`, pre-cron hardening |
| 2026-05-04 | Dashboard Phase 1 | `audit.html` — action item triage, archive with reason, collapsible raw text, shared CSS |

---

## Reference
- Full wiki plan: `plans/wiki_implementation.md`
- Full dashboard plan: `plans/dashboard_improvements_plan.md`
