# Roadmap — Ranked by System Impact

_Ranked 2026-07-20, updated 2026-07-24 (find_by_url shipped → Done; added the remaining open `mcp_improvements.md` items; folded the token burn dashboard into #4; bumped Project pages to #3 as work reliance grew and a project→wiki scoping gap surfaced)._ This is the priority ordering for `plans/in_progress/*.md`, ranked by how much each one improves the system — data correctness and compounding leverage first, then scoped-but-narrower fixes, then polish, then nice-to-haves. Not a schedule or a commitment to build all of it; pick from the top when starting new work. Re-rank in place (edit this file) whenever priorities shift — don't let it go stale like a second `CURRENT.md`. Day-to-day active/next-up tracking still lives in `CURRENT.md`; this file is the ordering, that file is the status. Every `plans/in_progress/*.md` should appear somewhere below (or in "Not ranked here") — if you add a plan file, add its entry.

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

## 3. Project pages
`plans/in_progress/project_page_implementation.md`

**Bumped up 2026-07-24 — increasingly used for work.** The core feature is built and working (project-type wiki pages: synopsis / status / decisions / history / open todos), but there's a **proven correctness gap**: some `category=project` thoughts silently don't appear on their project's wiki page. The anchor-topics grouping mechanism predates the `workspace` field (shipped 2026-07-10), so a project defined only by anchor topics misses workspace-scoped captures — e.g. the agile-backlog project has no page at all. The open **workspace-hybrid scoping follow-up** (`project_page_implementation.md` line 330, needs a grill-me) is the fix. As work reliance grows, projects not surfacing what's actually captured about them is the highest-value thing to close here.

## 4. AI token / cost tracker (+ token burn dashboard)
`plans/in_progress/ai_token_tracker.md`

Zero cost visibility exists today across 6 LLM/embedding call sites. Two phases in one plan: **Phase 1** instrumentation (`api_usage_log` table, pricing table, per-call logging) — also unblocks the Phase 2 contradiction-detection cost cap already assumed in `wiki_implementation.md`; **Phase 2** the Token Burn Dashboard (Nate B. Jones' framework — fidelity-labeled measurement table, cost-per-work-unit views, Tufte-clean charts, and a `/token-review` weekly-ritual skill). Phase 2's `/token-review` skill can ship the moment Phase 1 data exists, before any dashboard HTML.

## 5. Proactive resurfacing of external insights
`plans/in_progress/open_brain_improvements.md` (bottom stub)

Closes the biggest identified conceptual gap — retrieval/synthesis is entirely pull-based today. Design is agreed (relevance-linked, ~60% floor, one/day) but not implementation-ready.

## 6. Pan queue visibility — remainder
`plans/in_progress/mcp_improvements.md` §5 (items #1 + #3)

Discord-captured "pan this" videos still pile up invisibly. The query primitive shipped (`--pending-pans`/`get_pans`, 2026-07-11) and now `find_by_url` (§4, done 2026-07-24) supplies the canonical-URL infra these share. Two durable pieces remain: **#1** first-class `pan_status: open` tag at capture time (structural root fix), and **#3** an "🎬 Open pans (N)" section in the daily/weekly digest (passive recurring visibility). Scoped, proven-need, reuses just-built infra — the natural continuation of the find_by_url work.

## 7. Digest backlog filter
`plans/in_progress/digest_backlog_filter.md`

Fixes recap open-threads getting misclassified as urgent Top-3 actions. Chronic but tolerable — user already tunes around it manually. Design not finalized.

## 8. Dashboard improvements (remaining phases)
`plans/in_progress/dashboard_improvements_plan.md`

Mostly shipped. Remaining: inline `raw_text` edit in `audit.html`, Top 10 People chart, Wiki Pages tab.

## 9. Dashboard audit page (remaining phase 2)
`plans/in_progress/dashboard_audit_plan.md`

Phase 1 fully shipped. Phase 2 (inline edit) overlaps with #8's remaining item — same piece of work, tracked in two plans.

## 10. Cross-tool skill sync
`plans/in_progress/cross_tool_skill_sync.md`

Windows/Copilot CLI parity for `grill-me`/`recap`. Doesn't touch retrieval or data quality — quality-of-life for a secondary environment.

## 11. Recall-before-work skill
`plans/in_progress/recall_before_work_skill.md`

Its own write-up says it automates something the user already does well manually — lowest marginal value of the open stubs.

## 12. MCP inferential/context tools (exploratory, Phase 5)
`plans/in_progress/mcp_improvements.md` §1–3

Three Karpathy-wiki-inspired ideas, none scoped past a stub: **§1 `get_gaps`** (a tool that infers what knowledge/decisions the brain's goals imply but are missing — distinct from `get_context`'s retrieval), **§2 `skill`/persona thought category** (thoughts that influence AI responses instead of surfacing in search, injected into every `get_context`), and **§3 audit-history surfacing** (a review task: check whether `get_context`/`meeting_prep` exploit full capture history/recency, not just point-in-time semantic retrieval). Lowest marginal value / highest design uncertainty — all Phase 5.

---

## Not ranked here

- `wiki_implementation.md` — the wiki MVP itself is shipped; its own remaining follow-ups are individually represented above (#1) or deferred to a later Phase 2 (contradiction detection / typed edges, not yet its own plan).
- `mcp_improvements.md` §4 (`find_by_url`, done) and §6 (`get_stats` cap, done) — shipped; the file's still-open items are ranked at #6 and #12 above.
