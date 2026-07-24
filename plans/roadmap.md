# Roadmap — Ranked by System Impact

_Ranked 2026-07-20, updated 2026-07-21._ This is the priority ordering for `plans/in_progress/*.md`, ranked by how much each one improves the system — data correctness and compounding leverage first, then scoped-but-narrower fixes, then polish, then nice-to-haves. Not a schedule or a commitment to build all of it; pick from the top when starting new work. Re-rank in place (edit this file) whenever priorities shift — don't let it go stale like a second `CURRENT.md`. Day-to-day active/next-up tracking still lives in `CURRENT.md`; this file is the ordering, that file is the status.

---

## Done

- ~~`find_by_url` exact lookup tool~~ — shipped and verified 2026-07-24 (`mcp_improvements.md` §4, commit `d0d77b3`): migration 009 RPC + `find_by_url` MCP tool (canonicalizes YouTube→video-ID / other→host+path, paginated, status=all default) + `/pan` Step 0b rewired to use it. Ground-truth verified (`iUSdS-6uwr4`→39, `jwtpMSRAPAQ`→35/34/1, substack path→26, bare domain→532).
- ~~Fix `compile_wiki.py` silent 1000-row truncation~~ — implemented and verified 2026-07-21 (exact match to ground truth: 2011/2011 active thoughts, no duplicates; spot-checks on "AI agents"/Board Game Inventory/Meal Planner all exact). `plans/done/compile_wiki_pagination_bug.md`

---

## 1. Wire up weekly wiki compile cron
`plans/in_progress/wiki_weekly_cron.md`

Nearly done. Location/schedule decided, Steps 1–4 shipped, and the one-time full `--all` correction **completed 2026-07-24** (418 pages, 202m, 0 errors, $19.32; wiki grew 154→418, mirror pushed as `compiled_wiki` `6990c46`, completion Discord DM confirmed the UA-header fix). The adaptive-thinking question was A/B tested and closed as keep-disabled (`plans/done/wiki_thinking_ab_test.md`). **Only Step 5 remains:** re-run `setup_rpi.py` on the Pi to activate the already-added weekly cron — needs physical Pi access.

## 2. Wiki-first routing + automemory bridge
`plans/in_progress/wiki_routing_and_automemory_bridge.md`

Makes `get_context` surface compiled wiki knowledge instead of raw thought dumps, and pipes Claude Code's own auto-memory into the searchable brain. Compounds every session.

## 3. AI token / cost tracker
`plans/in_progress/ai_token_tracker.md`

Zero cost visibility exists today across 6 LLM/embedding call sites. Also unblocks the Phase 2 contradiction-detection cost cap already assumed in `wiki_implementation.md`.

## 4. Proactive resurfacing of external insights
`plans/in_progress/open_brain_improvements.md` (bottom stub)

Closes the biggest identified conceptual gap — retrieval/synthesis is entirely pull-based today. Design is agreed (relevance-linked, ~60% floor, one/day) but not implementation-ready.

## 5. Digest backlog filter
`plans/in_progress/digest_backlog_filter.md`

Fixes recap open-threads getting misclassified as urgent Top-3 actions. Chronic but tolerable — user already tunes around it manually. Design not finalized.

## 6. Dashboard improvements (remaining phases)
`plans/in_progress/dashboard_improvements_plan.md`

Mostly shipped. Remaining: inline `raw_text` edit in `audit.html`, Top 10 People chart, Wiki Pages tab.

## 7. Dashboard audit page (remaining phase 2)
`plans/in_progress/dashboard_audit_plan.md`

Phase 1 fully shipped. Phase 2 (inline edit) overlaps with #6's remaining item — same piece of work, tracked in two plans.

## 8. Project pages
`plans/in_progress/project_page_implementation.md`

Already built and working. Was blocked on the pagination bug — now unblocked (see Done above).

## 9. Cross-tool skill sync
`plans/in_progress/cross_tool_skill_sync.md`

Windows/Copilot CLI parity for `grill-me`/`recap`. Doesn't touch retrieval or data quality — quality-of-life for a secondary environment.

## 10. Recall-before-work skill
`plans/in_progress/recall_before_work_skill.md`

Its own write-up says it automates something the user already does well manually — lowest marginal value of the open stubs.

---

## Not ranked here

- `wiki_implementation.md` — the wiki MVP itself is shipped; its own remaining follow-ups are individually represented above (#1) or deferred to a later Phase 2 (contradiction detection / typed edges, not yet its own plan).
