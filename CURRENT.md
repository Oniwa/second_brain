# Current Work

## Active
**Nothing in flight.** `get_stats`, the recap safety rules, the recap CURRENT.md drift-check, the `workspace` project-scoping field, and the `get_pans` skill were just shipped (see Recently Shipped) — pick the next item from Up Next below.

---

## Up Next

### Proven bugs (highest priority — `plans/in_progress/mcp_improvements.md`)
- **`find_by_url` tool missing** — no way to look up a thought by URL; root cause of repeated pan-dedup false negatives (several videos looked "unpanned" on URL search when they'd already been fully panned). §4
- **Pan queue visibility, remainder** — §5 item 2's `--pending-pans` shipped 2026-07-11 as part of `get_pans`; the Discord `!pans` half and item #1's first-class `pan_status` field remain open

### Skill-only edits — no code, just `.md` files
- **`pan_skill_improvements.md`** → edit `.claude/commands/pan.md`: A1 intra-batch overlap check, A2 delete fetched transcript after pan, B1 make trims+merges proactive in Phase 2.5, B2 lower overlap floor 65%→~55% (real near-dups this week landed at 55–64%, invisible to the current threshold). A3 (creator-saturation nudge) was explicitly rejected — dense Nate B. Jones coverage is deliberate curation, not bloat.

### Follow-ups from the `workspace` field (shipped 2026-07-10, `plans/done/project_scoping_field.md`)
- **`scripts/brain.py` `--search`/`--recent` scoping** — same `workspace` filtering the MCP tools now have; deliberately deferred as lower priority in the plan
- **`.workspace=abucw` files in ABU repos** — one-time action outside this repo, needs doing on the work machine so multi-repo ABUCW captures land on one slug
- **`is_external` mislabeling cleanup** — ~213 rows have clearly external `source` (youtube/substack/etc.) but `is_external=false`; captured as a separate non-blocking bug during the workspace work, fix is a one-line `UPDATE` plus finding the capture path that drops the flag
- **Known gap, not a bug:** a handful of historical thoughts with generic `source` (e.g. plain `mcp`) couldn't be backfilled to a workspace and still appear in every scope — see the plan's "Known gap" note for options if this becomes annoying

### Carried over from May (still open)
- ~~Fix `project_definitions.json` anchor topics~~ — **misdiagnosed**, corrected 2026-07-03: anchors already match real `topics[]` tags. Real cause is a silent 1000-row PostgREST cap in `compile_wiki.py` (same bug class as the `get_stats` fix, different file) — see new stub below
- **Fix Discord DM 403** — bot returns Forbidden on DM; last pre-cron hardening item
- **Decide cron location** — Pi vs PC vs on-demand; blocks scheduling weekly wiki recompile
- **Dashboard item 11 — inline `raw_text` edit in `audit.html`** — no longer blocked (Edge Function update-mode shipped 5/05); just needs the Phase 2 UI (`plans/in_progress/dashboard_audit_plan.md`)

### Needs more design before implementing
- **`compile_wiki_pagination_bug.md`** (new stub) — same 1000-row PostgREST silent-cap bug as `get_stats`, now found in `compile_wiki.py` (`get_qualifying_projects` confirmed broken; `get_distinct_topics`/`get_distinct_people`/`fetch_thoughts_for_project` likely also undercounting). Bigger than the original "fix the JSON" task — needs a grill-me pass to scope (shared pagination helper vs. per-site fix, which of the 9 call sites to fix now vs. defer)
- **`digest_backlog_filter.md`** — recap-sourced open threads keep getting promoted to Top 3 actions; fix sketch exists (stamp `source: "recap"`, add `[BACKLOG]` bucket) but marker choice / promotion path / retroactive backfill are undecided
- **Proactive resurfacing of external insights** (`open_brain_improvements.md`, bottom) — relevance-linked design agreed (1 insight/day, ~60% relevance floor, gated) but not built; this is the actual fix for the "pull-only synthesis" gap identified in a 2026-07-02 brain-grading session (B+ retrieval, A- overall)
- **`recall_before_work_skill.md`** (stub) — `/start`-style skill to auto-pull relevant context at session start; distinct from the external-resurfacing item above (automates what the user already does well, vs. fixing what they can't query at all) — **unblocked 2026-07-10**, the `workspace` scoping mechanism it needed now exists and is verified working; still needs its own planning session for the remaining open questions (trigger mechanism, topic inference, digest overlap)
- **`cross_tool_skill_sync.md`** (new stub) — keep `grill-me`/`recap` in sync across Claude Code (Linux home) and GitHub Copilot CLI (Windows work) from one source-controlled copy in this repo; blocked on confirming Copilot's actual `.copilot/skills/<name>/` file layout and scope (repo vs. user-global) from the work PC — current `scripts/link_global_skills.py` is the superseded symlink-based approach, not yet rewritten
- **Concept-level dedup/merge** (`wiki_implementation.md`, bottom) — near-dup insights across sources still accrete unmerged; deferred to the Phase 2 `thought_edges` classifier; also needs to reconcile the 85% wiki-time threshold against pan's revised ~55% floor (B2 above)

---

## Recently Shipped
| Date | Item | What |
|---|---|---|
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
- Full wiki plan: `plans/in_progress/wiki_implementation.md`
- Full dashboard plan: `plans/in_progress/dashboard_improvements_plan.md` · audit page: `plans/in_progress/dashboard_audit_plan.md`
- MCP server plan: `plans/in_progress/mcp_improvements.md`
- Pan skill plan: `plans/in_progress/pan_skill_improvements.md`
- Recap skill plan (done): `plans/done/recap_skill_improvements.md` · follow-up stub: `plans/in_progress/recall_before_work_skill.md`
- Workspace field plan (done): `plans/done/project_scoping_field.md`
- `get_pans` skill plan (done): `plans/done/get_pans_skill.md`
- Digest backlog filter: `plans/in_progress/digest_backlog_filter.md`
- OB1 comparison / backlog stubs: `plans/in_progress/open_brain_improvements.md`
- Pan queue tracker: `open_pans.md`
- Project page grouping: `scripts/project_definitions.json`
