# Current Work

## Active
**Nothing in flight.** `get_stats` was just fixed (see Recently Shipped) — pick the next item from Up Next below.

---

## Up Next

### Proven bugs (highest priority — `plans/in_progress/mcp_improvements.md`)
- **`find_by_url` tool missing** — no way to look up a thought by URL; root cause of repeated pan-dedup false negatives (several videos looked "unpanned" on URL search when they'd already been fully panned). §4
- **Pan queue visibility** — Discord pan submissions are invisible to `semantic_search`/`list_recent`; quick win is `--pending-pans` / `!pans` (§5, item 2), durable fix is a first-class `pan_status` (§5, item 1)

### Skill-only edits — no code, just `.md` files
- **`pan_skill_improvements.md`** → edit `.claude/commands/pan.md`: A1 intra-batch overlap check, A2 delete fetched transcript after pan, B1 make trims+merges proactive in Phase 2.5, B2 lower overlap floor 65%→~55% (real near-dups this week landed at 55–64%, invisible to the current threshold). A3 (creator-saturation nudge) was explicitly rejected — dense Nate B. Jones coverage is deliberate curation, not bloat.
- **`recap_skill_improvements.md`** → edit `.claude/commands/recap.md`: add OB1 memory-safety rules (no transcript dumping, no reasoning traces, no silently-promoted standing instructions)

### Carried over from May (still open)
- **Fix `project_definitions.json` anchor topics** — Board Game Inventory and Meal Planner still compile with 0 thoughts; anchor keywords don't match actual `topics[]` tags
- **Fix Discord DM 403** — bot returns Forbidden on DM; last pre-cron hardening item
- **Decide cron location** — Pi vs PC vs on-demand; blocks scheduling weekly wiki recompile
- **Dashboard item 11 — inline `raw_text` edit in `audit.html`** — no longer blocked (Edge Function update-mode shipped 5/05); just needs the Phase 2 UI (`plans/in_progress/dashboard_audit_plan.md`)

### Needs more design before implementing
- **`digest_backlog_filter.md`** — recap-sourced open threads keep getting promoted to Top 3 actions; fix sketch exists (stamp `source: "recap"`, add `[BACKLOG]` bucket) but marker choice / promotion path / retroactive backfill are undecided
- **Proactive resurfacing of external insights** (`open_brain_improvements.md`, bottom) — relevance-linked design agreed (1 insight/day, ~60% relevance floor, gated) but not built
- **Concept-level dedup/merge** (`wiki_implementation.md`, bottom) — near-dup insights across sources still accrete unmerged; deferred to the Phase 2 `thought_edges` classifier; also needs to reconcile the 85% wiki-time threshold against pan's revised ~55% floor (B2 above)

---

## Recently Shipped
| Date | Item | What |
|---|---|---|
| 2026-07-03 | `get_stats` 1000-row cap fixed | Replaced client-side row tally with 4 independent `count: "exact", head: true` queries in `mcp/src/server.ts`; added drift warning if total ≠ active+archived+needs_review; verified against `execute_sql` ground truth (1856/1665/191/0, exact match). `mcp_improvements.md` §6 |
| 2026-07-02 | Pan backlog fully reconciled | 11 Discord-submitted videos (6/18–6/29) panned or closed out; `open_pans.md` resynced from DB via direct PostgREST query (MCP search tools miss these) |
| 2026-07-01–02 | Pan skill dedup hardening | URL-based dedup lookup + archive reminders added to `pan.md`; `open_pans.md` tracker created |
| 2026-07-02 | 4 new improvement plans written | `mcp_improvements.md`, `pan_skill_improvements.md`, `digest_backlog_filter.md`, plus stubs added to `open_brain_improvements.md` and `wiki_implementation.md` |
| 2026-05-18 | Digest external filter | Filter external (`is_external`) captures out of digest Top-3 and audit action items |
| 2026-05-18 | bot.py JWT fix | Use `SUPABASE_EDGE_FUNCTION_JWT` for edge function calls |
| 2026-05-18 | Repo reorg | `plans/` split into `in_progress`/`done`; `CURRENT.md` moved to project root |
| 2026-05-09 | Wiki portability + full recompile | Private git repo inside `compiled-wiki/`; 130+ pages regenerated with source labels, footnote citations, URLs, project pages |
| 2026-05-04 | Wiki MVP + Dashboard Phase 1 | `compile_wiki.py`, `wiki_pages` table, MCP wiki tools; `audit.html` action-item triage page |

---

## Reference
- Full wiki plan: `plans/in_progress/wiki_implementation.md`
- Full dashboard plan: `plans/in_progress/dashboard_improvements_plan.md` · audit page: `plans/in_progress/dashboard_audit_plan.md`
- MCP server plan: `plans/in_progress/mcp_improvements.md`
- Pan skill plan: `plans/in_progress/pan_skill_improvements.md`
- Recap skill plan: `plans/in_progress/recap_skill_improvements.md`
- Digest backlog filter: `plans/in_progress/digest_backlog_filter.md`
- OB1 comparison / backlog stubs: `plans/in_progress/open_brain_improvements.md`
- Pan queue tracker: `open_pans.md`
- Project page grouping: `scripts/project_definitions.json`
