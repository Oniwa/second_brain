# Roadmap — Ranked by System Impact

_Ranked 2026-07-20, updated 2026-07-26 (added #2 digest chunking fix — the weekly review DM was arriving silently truncated; #3 workspace correction + diagnostic, split out of the workspace-only project-scoping grill and gated behind #2 since they share the Discord DM path; #5 person identity resolution, after finding person naming unresolved system-wide; #7 wiki compile cost control, after one person page turned out to be half the compile bill; and moved Project pages to Done — workspace-only scoping shipped)._ This is the priority ordering for `plans/in_progress/*.md`, ranked by how much each one improves the system — data correctness and compounding leverage first, then scoped-but-narrower fixes, then polish, then nice-to-haves. Not a schedule or a commitment to build all of it; pick from the top when starting new work. Re-rank in place (edit this file) whenever priorities shift — don't let it go stale like a second `CURRENT.md`. Day-to-day active/next-up tracking still lives in `CURRENT.md`; this file is the ordering, that file is the status. Every `plans/in_progress/*.md` should appear somewhere below (or in "Not ranked here") — if you add a plan file, add its entry.

---

## Done

- ~~Project pages: workspace-only scoping~~ — grilled and shipped 2026-07-26 (`plans/done/project_page_implementation.md`). A project IS a `workspace`; anchor-topic grouping retired, projects auto-discovered from distinct `workspace` values (so "project exists but has no page" is now structurally impossible), page identity derived from the workspace slug rather than the display title, `project_definitions.json` demoted to an optional title-override map, one-time 29-row backfill (`010_workspace_backfill.sql`, idempotent). **8 project pages, 4 of them new** — including the agile-backlog project that triggered the whole plan. 44 pages recompiled, 0 errors, ~$3; mirror pushed (`compiled_wiki` `4ef6a16`). Follow-ons split out to #3, #5, and #7.
- ~~`find_by_url` exact lookup tool~~ — shipped and verified 2026-07-24 (`mcp_improvements.md` §4, commit `d0d77b3`): migration 009 RPC + `find_by_url` MCP tool (canonicalizes YouTube→video-ID / other→host+path, paginated, status=all default) + `/pan` Step 0b rewired to use it. Ground-truth verified (`iUSdS-6uwr4`→39, `jwtpMSRAPAQ`→35/34/1, substack path→26, bare domain→532).
- ~~Fix `compile_wiki.py` silent 1000-row truncation~~ — implemented and verified 2026-07-21 (exact match to ground truth: 2011/2011 active thoughts, no duplicates; spot-checks on "AI agents"/Board Game Inventory/Meal Planner all exact). `plans/done/compile_wiki_pagination_bug.md`

---

## 1. Wire up weekly wiki compile cron
`plans/in_progress/wiki_weekly_cron.md`

Location/schedule decided, Steps 1–4 shipped, and the one-time full `--all` correction **completed 2026-07-24** (418 pages, 202m, 0 errors, $19.32; wiki grew 154→418, mirror pushed as `compiled_wiki` `6990c46`, completion Discord DM confirmed the UA-header fix). The adaptive-thinking question was A/B tested and closed as keep-disabled (`plans/done/wiki_thinking_ab_test.md`). **Two things remain:** **Step 5** — re-run `setup_rpi.py` on the Pi to activate the weekly cron (needs physical Pi access); **Step 6 (new 2026-07-24)** — add `--git-publish` to `compile_wiki.py` so the cron commits+pushes the `compiled_wiki` mirror (today it has no git logic — the cron would regenerate pages only on the Pi's disk), plus confirm the `compiled_wiki` repo is cloned on the Pi with non-interactive push auth. Step 6 must be grilled before implementing (open sub-decisions: where the git logic lives; PAT vs SSH deploy key for non-interactive push auth).

## 2. Fix silent digest truncation (Discord DM chunking)
`plans/in_progress/digest_chunking_fix.md`

**New 2026-07-26.** The weekly review DM arrives cut off mid-sentence (~1900 chars) with no continuation. `send_discord_dm()` hard-slices the message at a fixed offset and fires the chunks back-to-back with no pacing — Discord 429-rate-limits the second message, `urlopen` raises, and the outer `except` swallows it after chunk 1 already shipped, so partial delivery is silent. Fix: boundary-aware splitter (no content dropped) + inter-chunk delay + 429 retry honoring `retry_after` + a real error when a chunk fails after retries. Small, high-certainty, no schema/infra change; ranked high because it's a correctness failure in a flagship output the user actually reads (Gmail copy is intact, so nothing is lost — but the primary channel is degraded).

## 3. Workspace correction + unscoped-capture diagnostic
`plans/in_progress/workspace_correction_and_diagnostic.md`

**New 2026-07-26**, split out of the workspace-only project-scoping grill. Workspace-only scoping fixes the old "project thoughts don't reach their page" bug but opens a narrower one: a thought captured outside its repo gets `workspace=NULL` and silently misses the page. Two gaps close together — `update_thought` **cannot edit `workspace` at all** today (so a mis-scoped thought is uncorrectable through any interface), and nothing reports project-category thoughts with a null workspace. A diagnostic without a correction path is just noise, hence one unit. Low urgency by measurement: nearly all capture goes through the `recap` skill from inside the repo, which derives workspace correctly. **Must ship after #2** — the diagnostic lands in the same Discord DM that currently truncates.

## 4. Wiki-first routing + automemory bridge
`plans/in_progress/wiki_routing_and_automemory_bridge.md`

Makes `get_context` surface compiled wiki knowledge instead of raw thought dumps, and pipes Claude Code's own auto-memory into the searchable brain. Compounds every session.

## 5. Person identity resolution — canonical names across the brain
`plans/in_progress/person_identity_dedup.md`

**New 2026-07-26.** Started as "the owner has two person pages"; measurement showed the owner is not a special case — **person identity is unresolved system-wide**. 117 distinct `people` values across 1556 mentions, in three failure modes: bare first names colliding with full names (8 clusters — `Simon` (7) could be `Simon Scrapes` (49) or `Simon Willison` (2)), case/punctuation variants (`Nate B. Jones` 639 · `Nate B Jones` 266 · `NateBJones` 1), and machine identifiers captured as people (`jbarksdale`, `rduictrsvc@leggett.com`, plus `danshapiro`/`simonwillison` leaking in from source prefixes). Critically, `people_aliases.json` fixes **wiki pages only** — 266 Nate mentions still carry the wrong string in `thoughts.people`, so every people-based query misses them. Needs a re-runnable detection report, data-layer canonicalization, and capture-time prevention — plus a design call on whether the owner should have a person page at all. Blocked on the same missing orphan-deletion path: ~15 merges means ~15 dead pages nothing cleans up.

## 6. AI token / cost tracker (+ token burn dashboard)
`plans/in_progress/ai_token_tracker.md`

Zero cost visibility exists today across 6 LLM/embedding call sites. Two phases in one plan: **Phase 1** instrumentation (`api_usage_log` table, pricing table, per-call logging) — also unblocks the Phase 2 contradiction-detection cost cap already assumed in `wiki_implementation.md`; **Phase 2** the Token Burn Dashboard (Nate B. Jones' framework — fidelity-labeled measurement table, cost-per-work-unit views, Tufte-clean charts, and a `/token-review` weekly-ritual skill). Phase 2's `/token-review` skill can ship the moment Phase 1 data exists, before any dashboard HTML.

## 7. Wiki compile cost control — page exclusion and recompile cadence
`plans/in_progress/wiki_compile_cost_control.md`

**Content-creator half shipped 2026-08-06** (grilled, implemented, verified against live production data). Quarterly cadence + `exclude` flag for the 33 content-creator person pages (classified live via ≥50% external-mention ratio) closes the original finding: `person-nate-b-jones` at 905 thoughts was 52% of a run's input volume and would have cost ~$1.40/week in perpetuity under plain `--skip-unchanged` (any `thought_count` delta triggers a full recompile). Measured resolution: the page is ~96% duplication of topic pages (deleting it would only orphan 32 thoughts, not 905), so cadence — not deletion — was chosen to preserve its one unique value (cross-topic framework synthesis), which is also the slowest-changing part of the page.

**New follow-up opened 2026-08-07, during the cron's first live activation run.** The any-delta-triggers-full-recompile problem the cadence fix solved for content-creator people turns out to be general — topics (and unverified, projects) still use the plain any-delta rule. First live run cost ~$4 and had to be resumed after an interrupt: ~40 topics had genuine but *tiny* deltas (+1 to +6 thoughts each, e.g. `AI skills` 13→14), yet each triggered a full re-synthesis of the page's entire thought volume — the big topics (`AI agents` 331, `prompt engineering` 138, `system design` 112, ...) accounted for essentially all of the cost. Unlike people, topics have **no duplication-based escape hatch** — measured directly (90%+ topic-to-topic overlap is normal multi-tagging, not redundancy, since topics are already the most-canonical layer) — so a delta-threshold fix here means accepting staleness on exactly the pages that are large *because* they're high-value.

**Leading candidate as of 2026-08-07: `plans/in_progress/wiki_incremental_compile.md`.** Synthesize from only the thoughts captured since the last compile plus the existing compiled page, instead of the full raw corpus every time. Quantified against real data (the actual `topic-ai-agents.md` file + this session's Sonnet 5 pricing): input tokens for a page like "AI agents" drop from ~128K (full corpus) to ~9-10K (existing page + delta), an ~85-90% reduction; modeled monthly cost drops from ~$20 to an estimated ~$3-5. No new platform or auth needed — builds on infrastructure already shipped this session. Real risk: quality drift over repeated incremental edits with no full reconsideration of the source data; mitigated by a periodic full-corpus re-baseline (candidate: quarterly, mirroring the people cadence). Needs a quality pilot (1-2 topics, incremental output vs. full resynthesis on the same data) before broader design.

**Fallback: `plans/in_progress/wiki_cowork_synthesis.md`.** Route expensive pages through Claude Cowork's Scheduled Tasks instead — confirmed subscription billing, genuine cloud-hosted scheduling, Supabase connector, full Windows parity. Sidesteps the drift question entirely (keeps full-resynthesis quality) but needs a new platform/auth and has unverified usage-pool/context-limit fit. Revisit only if incremental compile's drift risk proves unmanageable. The plain delta-threshold from this file remains the last-resort fallback if neither works out.

## 8. Proactive resurfacing of external insights
`plans/in_progress/open_brain_improvements.md` (bottom stub)

Closes the biggest identified conceptual gap — retrieval/synthesis is entirely pull-based today. Design is agreed (relevance-linked, ~60% floor, one/day) but not implementation-ready.

## 9. Pan queue visibility — remainder
`plans/in_progress/mcp_improvements.md` §5 (items #1 + #3)

Discord-captured "pan this" videos still pile up invisibly. The query primitive shipped (`--pending-pans`/`get_pans`, 2026-07-11) and now `find_by_url` (§4, done 2026-07-24) supplies the canonical-URL infra these share. Two durable pieces remain: **#1** first-class `pan_status: open` tag at capture time (structural root fix), and **#3** an "🎬 Open pans (N)" section in the daily/weekly digest (passive recurring visibility). Scoped, proven-need, reuses just-built infra — the natural continuation of the find_by_url work.

## 10. Digest backlog filter
`plans/in_progress/digest_backlog_filter.md`

Fixes recap open-threads getting misclassified as urgent Top-3 actions. Chronic but tolerable — user already tunes around it manually. Design not finalized.

## 11. Dashboard improvements (remaining phases)
`plans/in_progress/dashboard_improvements_plan.md`

Mostly shipped. Remaining: inline `raw_text` edit in `audit.html`, Top 10 People chart, Wiki Pages tab.

## 12. Dashboard audit page (remaining phase 2)
`plans/in_progress/dashboard_audit_plan.md`

Phase 1 fully shipped. Phase 2 (inline edit) overlaps with #8's remaining item — same piece of work, tracked in two plans.

## 13. Cross-tool skill sync
`plans/in_progress/cross_tool_skill_sync.md`

Windows/Copilot CLI parity for `grill-me`/`recap`. Doesn't touch retrieval or data quality — quality-of-life for a secondary environment.

## 14. Recall-before-work skill
`plans/in_progress/recall_before_work_skill.md`

Its own write-up says it automates something the user already does well manually — lowest marginal value of the open stubs.

## 15. MCP inferential/context tools (exploratory, Phase 5)
`plans/in_progress/mcp_improvements.md` §1–3

Three Karpathy-wiki-inspired ideas, none scoped past a stub: **§1 `get_gaps`** (a tool that infers what knowledge/decisions the brain's goals imply but are missing — distinct from `get_context`'s retrieval), **§2 `skill`/persona thought category** (thoughts that influence AI responses instead of surfacing in search, injected into every `get_context`), and **§3 audit-history surfacing** (a review task: check whether `get_context`/`meeting_prep` exploit full capture history/recency, not just point-in-time semantic retrieval). Lowest marginal value / highest design uncertainty — all Phase 5.

---

## Not ranked here

- `wiki_implementation.md` — the wiki MVP itself is shipped; its own remaining follow-ups are individually represented above (#1) or deferred to a later Phase 2 (contradiction detection / typed edges, not yet its own plan).
- `mcp_improvements.md` §4 (`find_by_url`, done) and §6 (`get_stats` cap, done) — shipped; the file's still-open items are ranked at #6 and #12 above.
