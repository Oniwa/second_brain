# Roadmap — Ranked by System Impact

_Ranked 2026-07-20._ This is the priority ordering for `plans/in_progress/*.md`, ranked by how much each one improves the system — data correctness and compounding leverage first, then scoped-but-narrower fixes, then polish, then nice-to-haves. Not a schedule or a commitment to build all of it; pick from the top when starting new work. Re-rank in place (edit this file) whenever priorities shift — don't let it go stale like a second `CURRENT.md`. Day-to-day active/next-up tracking still lives in `CURRENT.md`; this file is the ordering, that file is the status.

---

## 1. Fix `compile_wiki.py` silent 1000-row truncation
`plans/in_progress/compile_wiki_pagination_bug.md`

Proven, live data-correctness bug — the wiki compiler undercounts topics/people/projects across the board (same PostgREST `max-rows` cap already fixed once in `get_stats`). `wiki_implementation.md`'s own follow-up list independently ranks this #1. Blocks item #10 below.

## 2. Wire up weekly wiki compile cron
`plans/in_progress/wiki_weekly_cron.md`

Everything needed (hardening, exit codes, retry/backoff, `--skip-unchanged`) already shipped — the only blocker is a location decision that's been open since May. Sequenced after #1 so the first automated run compiles against correct counts.

## 3. Wiki-first routing + automemory bridge
`plans/in_progress/wiki_routing_and_automemory_bridge.md`

Makes `get_context` surface compiled wiki knowledge instead of raw thought dumps, and pipes Claude Code's own auto-memory into the searchable brain. Compounds every session.

## 4. `find_by_url` exact lookup tool
`plans/in_progress/mcp_improvements.md` §4

Small effort, fixes a proven recurring correctness bug in the weekly pan-dedup workflow.

## 5. AI token / cost tracker
`plans/in_progress/ai_token_tracker.md`

Zero cost visibility exists today across 6 LLM/embedding call sites. Also unblocks the Phase 2 contradiction-detection cost cap already assumed in `wiki_implementation.md`.

## 6. Proactive resurfacing of external insights
`plans/in_progress/open_brain_improvements.md` (bottom stub)

Closes the biggest identified conceptual gap — retrieval/synthesis is entirely pull-based today. Design is agreed (relevance-linked, ~60% floor, one/day) but not implementation-ready.

## 7. Digest backlog filter
`plans/in_progress/digest_backlog_filter.md`

Fixes recap open-threads getting misclassified as urgent Top-3 actions. Chronic but tolerable — user already tunes around it manually. Design not finalized.

## 8. Dashboard improvements (remaining phases)
`plans/in_progress/dashboard_improvements_plan.md`

Mostly shipped. Remaining: inline `raw_text` edit in `audit.html`, Top 10 People chart, Wiki Pages tab.

## 9. Dashboard audit page (remaining phase 2)
`plans/in_progress/dashboard_audit_plan.md`

Phase 1 fully shipped. Phase 2 (inline edit) overlaps with #8's remaining item — same piece of work, tracked in two plans.

## 10. Project pages
`plans/in_progress/project_page_implementation.md`

Already built and working. Blocked by #1 — resolves itself once the pagination fix ships.

## 11. Cross-tool skill sync
`plans/in_progress/cross_tool_skill_sync.md`

Windows/Copilot CLI parity for `grill-me`/`recap`. Doesn't touch retrieval or data quality — quality-of-life for a secondary environment.

## 12. Recall-before-work skill
`plans/in_progress/recall_before_work_skill.md`

Its own write-up says it automates something the user already does well manually — lowest marginal value of the open stubs.

---

## Not ranked here

- `wiki_implementation.md` — the wiki MVP itself is shipped; its own remaining follow-ups are individually represented above (#1, #2) or deferred to a later Phase 2 (contradiction detection / typed edges, not yet its own plan).
