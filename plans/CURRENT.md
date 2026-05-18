# Current Work

## Active
**Fix `project_definitions.json` anchor topics**

Board Game Inventory and Meal Planner compiled with 0 thoughts — the anchor topic keywords in `scripts/project_definitions.json` don't match the actual `topics[]` tags on those project thoughts. Need to query those thoughts, identify correct tags, update anchors.

Steps:
1. Query active project thoughts filtered to Board Game Inventory / Meal Planner (by title keyword or people[])
2. Inspect actual `topics[]` values
3. Update `scripts/project_definitions.json` with correct anchor topics
4. Re-run `--project "Board Game Inventory" --project "Meal Planner"` to confirm non-zero output

---

## Up Next
- **Fix Discord DM 403** — bot returns Forbidden on DM; last remaining pre-cron hardening item; need to investigate bot permissions / DM channel access
- **Wiki item 3 — Project pages** — Board Game Inventory and Meal Planner pages are currently empty; also need to decide if more projects should be added to `project_definitions.json`
- **Wiki item 1 — Cron location** — Pi vs PC vs on-demand; blocks scheduling weekly recompile
- **Dashboard item 11** — Inline `raw_text` edit in `audit.html` (backend is live, UI only)

---

## Recently Shipped
| Date | Item | What |
|---|---|---|
| 2026-05-09 | Wiki portability | Private git repo initialised inside `compiled-wiki/` — push/pull to sync wiki across machines |
| 2026-05-09 | Full wiki recompile | All 130+ pages regenerated with `is_external` source labels, footnote citations, URLs, project pages |
| 2026-05-09 | compile_wiki.py hardening | 300s timeout, 429 TPM retry with 65s backoff (3 attempts), `--skip-unchanged` for cron |
| 2026-05-09 | Wiki item 2 (step 5) | Recompiled all wiki pages with footnote citations and `[Source: ...]` labels |
| 2026-05-09 | URL + footnote citations | `urls` and `is_external` wired into all three compile paths; markdown `[^N]` footnote format |
| 2026-05-05 | Wiki item 2 (steps 1-4) | `is_external` column + backfill, Edge Function accepts flag, MCP `capture_thought` passes it, `get_thought` surfaces it, pan skill updated |
| 2026-05-05 | Dashboard 8-10 | Edge Function update mode (`id` param), MCP `updateThought` re-routes through Edge Function, Discord `!update` command |
| 2026-05-04 | Wiki MVP | `compile_wiki.py`, `wiki_pages` table, MCP `get_wiki_page` + `list_wiki_pages`, pre-cron hardening |
| 2026-05-04 | Dashboard Phase 1 | `audit.html` — action item triage, archive with reason, collapsible raw text, shared CSS |

---

## Reference
- Full wiki plan: `plans/wiki_implementation.md`
- Full dashboard plan: `plans/dashboard_improvements_plan.md`
- Project page grouping: `scripts/project_definitions.json`
