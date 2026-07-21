# compile_wiki.py — Silent 1000-Row Truncation (Same Bug Class as `get_stats`, Different Blast Radius)

**Status:** diagnosed 2026-07-03, **scoped via grill-me 2026-07-21 — ready to implement.** All open design questions below are resolved; see "Final Design" for the build spec.

---

## Final Design (resolved via grill-me 2026-07-21)

**1. Fix location — shared helper, not per-call-site.** Pagination is built into `supabase_get()` itself, so all 9 call sites in this file are fixed by one change, current and future. No caller currently wants a true capped/top-N result — every one of the 9 sites conceptually wants "every row matching this filter" — so a transparent full-fetch fix is correct for all of them with no exceptions to carve out.

**2. Mechanism — offset/limit loop, not Range header.** `supabase_get()` internally loops issuing GETs with `offset=0,1000,2000,...` (page size capped at 1000, matching `supabase/config.toml`'s `max_rows = 1000`) until a page returns fewer rows than requested, then concatenates all pages. No response-header parsing needed (rejected the `Range`/`Content-Range` alternative — no benefit here big enough to justify inspecting headers when the exhaustion signal from page-length is sufficient). The caller-facing `limit` parameter keeps its current meaning (max total rows desired across all pages) — **zero changes needed at any of the 9 call sites for the pagination logic itself.**

**3. Ordering — `id.asc` tiebreaker everywhere.** Offset-based pagination is only correct if row order is stable between page requests. `thoughts.id` and `wiki_pages.slug`-backed rows are unique per row, so append `,id.asc` to every paginated query's `order` param (as a secondary key where an order already exists, e.g. `fetch_thoughts_for_project`'s `created_at.desc`; as the sole key where none exists yet, e.g. `get_qualifying_projects`, `get_distinct_topics`, `get_distinct_people`, `get_unmatched_project_thoughts`, `get_existing_pages`). This is a small edit at each call site (add/extend the `order` param), separate from the pagination-loop change inside `supabase_get()`.

**4. Safety cap — hard abort past 50,000 rows.** A generous ceiling (~15-30x current corpus size) that will never fire under normal growth, but converts a hypothetical "server keeps returning data" bug into a loud `RuntimeError` instead of a silent runaway loop.

**5. Scope — all 9 call sites in one pass.** Free consequence of fixing the shared helper; no "confirmed-broken now, latent-risk-later" split to track or revisit.

**6. Cost — self-resolving, no explicit budget needed.** The loop only issues a 2nd+ request when a specific query actually has >1000 matching rows. Today that's only `get_qualifying_projects`, `get_distinct_topics`, `get_distinct_people`, and `fetch_thoughts_for_project` (the four corpus-wide-unfiltered functions) — so a full `--all` run adds roughly 1-2 extra HTTP round trips total, not per-page-compiled. Filtered per-topic/per-person queries stay single-request as long as no single topic/person exceeds 1000 thoughts.

**7. Verification — total-count match + spot-checks.** The per-topic/per-person tally logic in `get_distinct_topics`/`get_distinct_people` was never itself buggy — it faithfully counts whatever thoughts happen to be in memory. The only bug is incomplete fetch. So:
   - Primary check: after the fix, the total row count fetched by `get_qualifying_projects`/`get_distinct_topics`/`get_distinct_people` must equal the true active-thought count from `execute_sql` ground truth (mirrors how the `get_stats` fix was verified).
   - Additional spot-checks: verify 2-3 specific known values via direct `execute_sql` queries — at minimum, Meal Planner and Board Game Inventory project counts (the two that originally exposed this bug) and one high-volume topic (e.g. "AI agents", ~151 thoughts, to confirm no off-by-one at a page boundary).
   - `--all --dry-run` should list Meal Planner and Board Game Inventory as qualifying projects (both previously showed 0/2 due to the truncation), and the printed `total active fetched:` debug line (if kept) should match ground truth.

**Not in scope for this pass** (explicitly deferred, not forgotten):
- The `UNMATCHED PROJECT THOUGHTS` list surfaced by `--dry-run` (expanding `project_definitions.json` coverage) is a separate, legitimate follow-up task — not conflated with this pagination fix.
- The "fetch-all-then-filter-in-Python" architecture of `get_qualifying_projects`/`fetch_thoughts_for_project` (fetch every active thought, then filter client-side by anchor topic) is a separate efficiency question from the truncation bug itself. Fixing pagination makes it *correct*; it doesn't change that it's still fetching more than a server-side-filtered query would need to. Not addressed here — flagged for a future pass if it ever becomes a real cost/latency problem at current corpus scale (~1,665-3,000 active thoughts), which it isn't yet.

---

## How this was found

Started as the "fix `project_definitions.json` anchor topics" task carried over from May (`CURRENT.md`, `wiki_implementation.md` Follow-Up Items #1) — the working theory was that Board Game Inventory / Meal Planner project pages compiled with 0 thoughts because the anchor keywords didn't match real `topics[]` tags.

**That diagnosis is wrong.** Direct verification via `get_thought` on the actual candidate thoughts showed the anchors already match exactly:
- `e09a47b0` (Meal Planner candidate) has topic `meal planning` — already an anchor
- `cf7aeafb` (Meal Planner candidate) has topics `meal planning`, `nutrition` — both already anchors
- `4bafbb90` / `4c364fcd` (Board Game Inventory candidates) have topic `board games` — already an anchor
- `17a2a863` (Board Game Inventory candidate) has topic `board game collection` — already an anchor

So `project_definitions.json` needs **no edit**. Debugging `get_qualifying_projects` directly (`scripts/compile_wiki.py:527-540`) found the real cause:

```
total active fetched: 1000
Meal Planner -> 0 matches; anchor_set= {'meal planning', 'health metrics', 'fitbit integration', 'django', 'nutrition'}
Board Game Inventory -> 2 matches; anchor_set= {'board game collection', 'board games', 'board game inventory'}
```

**`total active fetched: 1000`** — this is the exact same PostgREST `max-rows`-default-1000 bug just fixed in `mcp_improvements.md` §6 (`get_stats`), now independently present in `compile_wiki.py`. The real active-thought count is 1665 (confirmed via `execute_sql` ground truth during the `get_stats` fix). `get_qualifying_projects` requests `"limit": "2000"` but silently receives only 1000 rows back, with **no explicit `order` clause**, so it's an arbitrary slice of the corpus — not even reliably "oldest 1000" or "newest 1000."

Board Game Inventory's 2 matching thoughts (captured 3/6 and 3/8 — early in the corpus) happened to land inside whatever 1000-row slice came back. Meal Planner's matches did not. **This was luck, not correctness** — the fix that "worked" for Board Game Inventory was never actually fetching the full corpus either.

---

## Full scope — every `supabase_get` call site with a `limit` param

`supabase_get` (`compile_wiki.py:268`) is a single, shared, **non-paginating** HTTP helper — one request, whatever `limit` is passed, no loop, no `Range` header, no check for whether more rows exist beyond what came back. Every caller is equally exposed to the same silent cap. Full inventory:

| Function | Line | Limit requested | Query shape | Risk today |
|---|---|---|---|---|
| `get_qualifying_projects` | 532 | 2000 | **unfiltered**, all active thoughts | **Confirmed broken** — capped at 1000 vs real 1665 active |
| `get_distinct_topics` | 503 | 2000 | filtered `category != admin`, all matching thoughts | Same cap applies — topic counts across the board are likely undercounted, just not visibly broken (a topic sitting under-threshold due to undercount wouldn't look wrong, just silently wouldn't compile) |
| `get_distinct_people` | 517 | 2000 | **unfiltered**, all active thoughts | Same as above — person counts likely undercounted |
| `fetch_thoughts_for_project` | 436-444 | 500 | **unfiltered**, all active thoughts, client-side anchor filter | Same anti-pattern as `get_qualifying_projects` (fetch-all-then-filter), just capped at 500 instead of 2000 → 1000. Whatever slice comes back may disagree with what `get_qualifying_projects` sees, since there's no shared cursor/order between them |
| `get_unmatched_project_thoughts` | 543-552 | 500 | filtered `category = project` | Lower risk — server-side filtered to just project-category thoughts, a smaller universe. Real count not yet checked against the 500 cap |
| `fetch_thoughts_for_topic` | 415-422 | 500 | filtered `topics @> {topic}` | Low risk today — GIN-filtered to one topic; biggest topic currently is "AI agents" at ~151, well under 500 |
| `fetch_thoughts_for_person` | 425-432 | 500 | filtered `people @> {person}` | Low risk today, same reasoning |
| `get_existing_pages` | 555-559 | 1000 | all `wiki_pages` rows | Low risk today (~200 pages exist), same latent pattern as the wiki grows |
| `cmd_list` | ~658-662 | 1000 | all `wiki_pages` rows | Same as above |

**Takeaway:** this isn't a two-project-page bug, it's a systemic gap in how this file talks to Supabase. The two functions that fetch the *entire active corpus unfiltered* (`get_qualifying_projects`, `get_distinct_topics`, `get_distinct_people`, `fetch_thoughts_for_project`) are already past or approaching the 1000-row cliff (1665 real active thoughts); the filtered-query functions are safe today only because no single topic/person/project-category slice happens to exceed their limit yet — same class of latent risk as the `get_stats` bug looked like before anyone checked.

---

## Why the `get_stats` fix doesn't transfer directly

`get_stats`'s fix (`mcp_improvements.md` §6) replaced row-fetch-and-tally with `count: "exact", head: true` — cheap, cap-immune, but **returns no rows, only a count.** That works for `get_stats` because it only ever needed a number.

Every function above needs **actual row data** (`topics`, `people`, `title`, full thought content for page synthesis) — a count-only query can't substitute. The real fix has to be **actual pagination**: loop fetching pages (via `Range` headers or repeated `offset`/`limit` requests) until a page returns fewer rows than requested, accumulating the full result set client-side. This is a different, slightly more involved fix than `get_stats`' one-liner.

---

## Open questions for the grill-me session (not resolved — this is a stub)

All resolved 2026-07-21 via grill-me — see "Final Design" above for the decisions. Kept here for the historical record of what was actually asked:

- ~~Shared helper vs. per-call-site fix.~~ → shared helper (Final Design #1)
- ~~Explicit ordering.~~ → `id.asc` tiebreaker everywhere (Final Design #3)
- ~~Cost/performance.~~ → self-resolving, no explicit budget needed (Final Design #6)
- ~~Scope of this pass.~~ → all 9 sites together, free consequence of the shared-helper fix (Final Design #5)
- ~~Filtered-query functions — fix now or leave as latent risk?~~ → fixed now, for free, alongside everything else (Final Design #5)
- ~~Verification approach for functions with no single known-wrong number.~~ → total-count match (proof by construction, since the tally logic itself was never buggy) + spot-checks on Meal Planner/Board Game Inventory/a high-volume topic (Final Design #7)
- **Relationship to the `UNMATCHED PROJECT THOUGHTS` list** — the dry-run surfaced ~19 project-category thoughts not covered by any current project definition (e.g. "Add voice dictation to second brain," "Build NAS with Raspberry Pi controller"). Confirmed out of scope for this pass (see Final Design, "Not in scope") — a separate, legitimate task once the underlying data is trustworthy.

---

## Related

- `mcp_improvements.md` §6 — the `get_stats` fix that surfaced this same root-cause pattern; already resolved there, now recurring here
- `wiki_implementation.md` Follow-Up Items #1 — the original (incorrect) "fix anchor topics" framing; should be corrected once this plan is scoped, cross-referencing this file
- `CURRENT.md` "Carried over from May" — same correction needed
