# Current Work

## Active
**Wiki weekly cron Step 2 (manual `--all` correction) attempted 2026-07-22 and failed — 1/418 pages compiled.** Two bugs found and fixed during the attempt (see `plans/in_progress/wiki_weekly_cron.md` Update): `OUTPUT_DIR` pointed at a nonexistent `compiled-wiki` (hyphen) instead of the real git-tracked `compiled_wiki` (underscore) repo; and the same-day Sonnet 4.6→5 upgrade broke response parsing because Sonnet 5 defaults to adaptive thinking on (Sonnet 4.6 defaulted off), so `content[0]` was often a `thinking` block, not `text` — 19/418 pages made real billed calls (~$4) that then threw `KeyError: 'text'`. Both fixed: thinking explicitly disabled + parsing now scans for the text block by type, across all 3 Sonnet call sites (`compile_wiki.py`, `process-thought`, `generate-digest`). Separately, ~397/418 failed on an unrelated local DNS blip (unbilled).

**Not yet re-run.** Two things to resolve first: (1) `plans/in_progress/wiki_thinking_ab_test.md` (new stub) — whether adaptive thinking should actually be enabled for wiki synthesis specifically is untested, disabled is a safety default not a decision; (2) verify `compiled_wiki` resolves correctly as a sibling dir to `scripts/` on the Linux machine before running there (only verified on Windows so far). Once resolved: run the new **Step 2 smoke test** (3 single-entity real calls — `--topic "AI agents"`, `--person "Tammy"`, `--project "Second Brain"` — cheap way to catch any other lurking Sonnet-5-migration bugs before re-spending on all 418 pages), then re-run `compile_wiki.py --all` (or `--all --skip-unchanged` — "documentation" already succeeded and has a correct `thought_count`), then finish the cron plan's Step 5 (re-run `setup_rpi.py` on the Pi to pick up the cron job already added to it).

---

## Up Next

**Priority order lives in `plans/roadmap.md`** (ranked 2026-07-20) — start from the top there when picking new work. The groupings below are by blocker type, not priority; don't treat list order in this section as sequencing.

### Proven bugs (highest priority — `plans/in_progress/mcp_improvements.md`)
- **`find_by_url` tool missing** — no way to look up a thought by URL; root cause of repeated pan-dedup false negatives (several videos looked "unpanned" on URL search when they'd already been fully panned). §4
- **Pan queue visibility, remainder** — §5 item 2's `--pending-pans` shipped 2026-07-11 as part of `get_pans`; the Discord `!pans` half and item #1's first-class `pan_status` field remain open

### Follow-ups from the `workspace` field (shipped 2026-07-10, `plans/done/project_scoping_field.md`)
- **`scripts/brain.py` `--search`/`--recent` scoping** — same `workspace` filtering the MCP tools now have; deliberately deferred as lower priority in the plan
- **`.workspace=abucw` files in ABU repos** — one-time action outside this repo, needs doing on the work machine so multi-repo ABUCW captures land on one slug
- **`is_external` mislabeling cleanup** — ~213 rows have clearly external `source` (youtube/substack/etc.) but `is_external=false`; captured as a separate non-blocking bug during the workspace work, fix is a one-line `UPDATE` plus finding the capture path that drops the flag
- **Known gap, not a bug:** a handful of historical thoughts with generic `source` (e.g. plain `mcp`) couldn't be backfilled to a workspace and still appear in every scope — see the plan's "Known gap" note for options if this becomes annoying

### Carried over from May (still open)
- ~~Fix `project_definitions.json` anchor topics~~ — **misdiagnosed**, corrected 2026-07-03, and the real cause (1000-row PostgREST cap) is now **fixed 2026-07-21** — see Recently Shipped
- **Fix Discord DM 403** — root cause found 2026-07-22: `compile_wiki.py` `send_discord_dm` sends no `User-Agent`, so urllib's default UA gets 403'd (digest.py sets one and works). One-line fix, folded into the wiki_weekly_cron plan (Step 1); not yet applied
- ~~**Decide cron location**~~ — **resolved 2026-07-22: the Pi** (same runtime deps as the existing digest/nudge/remind jobs). See `plans/in_progress/wiki_weekly_cron.md`
- **Dashboard item 11 — inline `raw_text` edit in `audit.html`** — no longer blocked (Edge Function update-mode shipped 5/05); just needs the Phase 2 UI (`plans/in_progress/dashboard_audit_plan.md`)

### Needs more design before implementing
- **`ai_token_tracker.md`** (new stub, 2026-07-20) — zero cost/token visibility exists across the 6 LLM/embedding call sites today; needs a planning session (table vs. log file, shared TS/Python logging path, pricing table maintenance)
- **`digest_backlog_filter.md`** — recap-sourced open threads keep getting promoted to Top 3 actions; fix sketch exists (stamp `source: "recap"`, add `[BACKLOG]` bucket) but marker choice / promotion path / retroactive backfill are undecided
- **Proactive resurfacing of external insights** (`open_brain_improvements.md`, bottom) — relevance-linked design agreed (1 insight/day, ~60% relevance floor, gated) but not built; this is the actual fix for the "pull-only synthesis" gap identified in a 2026-07-02 brain-grading session (B+ retrieval, A- overall)
- **`recall_before_work_skill.md`** (stub) — `/start`-style skill to auto-pull relevant context at session start; distinct from the external-resurfacing item above (automates what the user already does well, vs. fixing what they can't query at all) — **unblocked 2026-07-10**, the `workspace` scoping mechanism it needed now exists and is verified working; still needs its own planning session for the remaining open questions (trigger mechanism, topic inference, digest overlap)
- **`cross_tool_skill_sync.md`** (new stub) — keep `grill-me`/`recap` in sync across Claude Code (Linux home) and GitHub Copilot CLI (Windows work) from one source-controlled copy in this repo; blocked on confirming Copilot's actual `.copilot/skills/<name>/` file layout and scope (repo vs. user-global) from the work PC — current `scripts/link_global_skills.py` is the superseded symlink-based approach, not yet rewritten
- **Concept-level dedup/merge** (`wiki_implementation.md`, bottom) — near-dup insights across sources still accrete unmerged; deferred to the Phase 2 `thought_edges` classifier. The pan-time/wiki-time threshold reconciliation is done (both now 85%/55%, 2026-07-12); open question is only whether the future edge-classifier should share that threshold or use its own

---

## Recently Shipped
| Date | Item | What |
|---|---|---|
| 2026-07-22 | Sonnet 4.6 → 5 model upgrade | Upgraded `SONNET_MODEL` to `claude-sonnet-5` in `compile_wiki.py` and redeployed the `process-thought` (v13) and `generate-digest` (v5) edge functions with the same change, preserving each function's existing `verify_jwt` setting. Haiku left untouched (`claude-haiku-4-5` already current). Chosen over staying on 4.6 because Sonnet 5's introductory pricing ($2/$10 per MTok through 2026-08-31) undercuts 4.6's standard rate ($3/$15) despite Sonnet 5's new tokenizer running ~30% more tokens for the same text |
| 2026-07-22 | Wiki `--all` correction attempt: 2 bugs found + fixed | First real run of the pagination-fix correction failed almost entirely (1/418 pages) — see Active above and `wiki_weekly_cron.md` Update for the full root-cause writeup (`OUTPUT_DIR` folder mismatch + Sonnet 5's adaptive-thinking-on-by-default silently breaking `content[0].text` parsing on 19 pages, ~$4 billed and wasted). Both fixed; whether to enable thinking for wiki synthesis specifically is now its own open question — `plans/in_progress/wiki_thinking_ab_test.md` |
| 2026-07-22 | Weekly wiki cron plan finalized | Grill-me pass resolved all open questions in `plans/in_progress/wiki_weekly_cron.md` (committed `cbf2424`): runs on the **Pi** (settling the May "decide cron location" blocker — same runtime deps as digest/nudge/remind), **Sunday 3am** `0 3 * * 0`, command `--all --skip-unchanged` with **no `--strict`** (systemic 401/403/529 errors already exit 1 on their own; `--strict` would only false-alarm on single-page flakes). Two findings: the Discord DM 403 is a **missing `User-Agent` header** (one-line fix folded in as Step 1), and the first `--all` run is an unavoidable one-time ~417-page spend (`--skip-unchanged` keys on `thought_count`, which the pagination fix changed everywhere) — so it's run manually + watched before enabling the cron. Step 1 (UA fix) and Step 3 (cron job added to `setup_rpi.py`) shipped same day |
| 2026-07-21 | `compile_wiki.py` pagination fix | Scoped via grill-me, then implemented: `supabase_get()` now transparently paginates past PostgREST's `max_rows=1000` cap (offset/limit loop, `id.asc` tiebreaker on all 9 call sites, 50k safety abort). Verified exact match to `execute_sql` ground truth (2011/2011 active thoughts, no duplicates); spot-checks on "AI agents" (330, was undercounted to 108), Board Game Inventory (3, was 0), Meal Planner (2, was 0) all exact. `--all --dry-run` now reports 417 qualifying pages vs. ~130 previously — most topic/person counts were undercounted, not just the two projects that originally exposed the bug. No full recompile run yet (real-cost action, deliberately deferred). `plans/done/compile_wiki_pagination_bug.md` |
| 2026-07-12 | Pan skill rework (B1/B2) | `/grill-me` review of `pan_skill_improvements.md` resolved all open items: A1 (intra-batch overlap) dissolved as a non-issue once B2 shipped; A2 (transcript litter) traced to a real bug in the separate `youtube_transcript` project (`main.py` wrote output relative to caller's CWD instead of its own `transcripts/` folder) — fixed there, tests updated (95/95 passing), committed and pushed to that repo's `origin/development` (`0fc0af2`); A3 stays rejected. B1 shipped as two narrated sub-steps in `pan.md` Phase 2.5 (merge check before drafting, recommended-trims pass after), both riding the existing single confirm gate. B2 shipped: overlap bands recalibrated to hard ≥85% / soft 55–84% / silent <55% (from a 65% floor that hid real near-dupes landing at 55–64%), reconciled into `wiki_implementation.md`'s matching spec. Plan moved to `plans/done/pan_skill_improvements.md`; live-batch verification deliberately deferred, not blocking |
| 2026-07-11 | `get_pans` skill | Haiku-driven skill (snake_case naming, new convention) that regenerates `open_pans.md` from the live brain — replaces manual reconciliation. `brain.py --pending-pans` runs the deterministic structural query (`source=discord` + has URL + `status=active`); confirmed via ground-truth review that this alone is the complete, correct set (no intent-classification needed — an initial attempt to exclude "generic-sounding" saves was wrong on review). Verified exact match against a hand-built 19-item baseline. `disable-model-invocation: true` so it only runs on explicit `/get_pans`, not autonomously. `plans/done/get_pans_skill.md`; supersedes/completes `mcp_improvements.md` §5 items #2 and #5 |
| 2026-07-10 | `workspace` project-scoping field | Nullable `thoughts.workspace` column (migration `007`), derived client-side at capture time (external-gate → `.workspace` override file → git-toplevel basename → cwd basename → null) in MCP `captureThought` — covers direct captures + `/recap` + `/pan` for free, both call the same function. All 4 MCP query tools (`semantic_search`, `list_recent`, `get_context`, `meeting_prep`) now scope to `<current> + global` by default with a `workspace:"all"` override and a `scope:` header; `semantic_search` RPC extended (migration `008`). Backfill: `agile_backlog_builder`=19, `abucw`=18, `idea_center_ai_policy`=21 (extended from the plan's original 6 — see plan for reasoning). Verified live end-to-end. `plans/done/project_scoping_field.md` |
| 2026-07-03 | Recap CURRENT.md drift check | Step 4 added to `recap.md`: compares CURRENT.md's Active/Up Next against session git history, flags a specific mismatch as a question, never auto-edits — flag-only by design |
| 2026-07-03 | Global skill portability | `grill-me.md` added to repo as canonical source (was global-only, Opus 4.8); stale global `pan.md` and `meal_planner`'s outdated `grill-me.md` reconciled; `cross_tool_skill_sync.md` stub written for Claude Code + Copilot CLI sync across Linux/Windows (design not finalized — see Up Next) |
| 2026-07-03 | Recap memory-safety rules | Added OB1-derived rules to `.claude/commands/recap.md`: no transcript dumps, no reasoning traces, no silently-captured standing instructions (disambiguated from open-thread TODOs and from decisions merely phrased like commands); self-reporting safety-check line added to the summary template. Plan moved to `plans/done/` |
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
- **Priority ranking:** `plans/roadmap.md`
- Full wiki plan: `plans/in_progress/wiki_implementation.md`
- Weekly wiki cron stub: `plans/in_progress/wiki_weekly_cron.md`
- Wiki thinking A/B test stub: `plans/in_progress/wiki_thinking_ab_test.md`
- AI token/cost tracker stub: `plans/in_progress/ai_token_tracker.md`
- Full dashboard plan: `plans/in_progress/dashboard_improvements_plan.md` · audit page: `plans/in_progress/dashboard_audit_plan.md`
- MCP server plan: `plans/in_progress/mcp_improvements.md`
- Pan skill plan (done): `plans/done/pan_skill_improvements.md`
- Recap skill plan (done): `plans/done/recap_skill_improvements.md` · follow-up stub: `plans/in_progress/recall_before_work_skill.md`
- Workspace field plan (done): `plans/done/project_scoping_field.md`
- `get_pans` skill plan (done): `plans/done/get_pans_skill.md`
- Digest backlog filter: `plans/in_progress/digest_backlog_filter.md`
- OB1 comparison / backlog stubs: `plans/in_progress/open_brain_improvements.md`
- Pan queue tracker: `open_pans.md`
- Project page grouping: `scripts/project_definitions.json`
