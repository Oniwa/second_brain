# compile_wiki.py — Silent 1000-Row Truncation (Same Bug Class as `get_stats`, Different Blast Radius)

**Status:** newly diagnosed 2026-07-03, **not yet planned in detail — needs a grill-me pass before implementation.** Do not implement from this write-up alone.

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

- **Shared helper vs. per-call-site fix.** Should `supabase_get` itself gain pagination (transparent to every caller, fixes all 9 sites at once), or should only the confirmed-broken/highest-risk sites get a bespoke paginating variant? A shared fix is more thorough but touches a lower-level helper used everywhere in the file — larger blast radius to review.
- **Explicit ordering.** Should every paginating query get an explicit `order` clause (most don't have one today, e.g. `get_qualifying_projects`) so pagination is deterministic and reproducible, independent of this fix?
- **Cost/performance.** Fetching 1665+ rows via repeated ~1000-row pages means at least 2 round-trips for the corpus-wide queries today, more as the brain grows. Compare against this file's existing cost-consciousness elsewhere (`--skip-unchanged` for cron efficiency) — does this fix need its own cost-awareness, or is 2-3 extra HTTP round-trips per `--all` run a non-issue?
- **Scope of this pass.** Fix only the confirmed-broken `get_qualifying_projects` now (minimal, matches the original task's urgency), or fix all corpus-wide-unfiltered functions in one pass since they're the same bug (`get_distinct_topics`, `get_distinct_people`, `fetch_thoughts_for_project`)? Leaning toward all four together since they share one root cause and one fix shape, but not decided.
- **Filtered-query functions** (`fetch_thoughts_for_topic`, `fetch_thoughts_for_person`, `get_unmatched_project_thoughts`, `get_existing_pages`, `cmd_list`) — fix now defensively even though not yet broken, or leave as a documented latent risk (like the `get_stats` window-fetch comment) and revisit if/when a query actually crosses its limit?
- **Verification approach** — after the fix, `get_qualifying_projects`'s debug script should report `total active fetched: 1665` (or whatever the live count is at fix time) and Meal Planner should show ≥2 matches; `--all --dry-run` should list 4 qualifying projects instead of 3. What's the equivalent verification for the topic/people count functions, given there's no single "known wrong number" to check them against the way `get_stats` had ground truth via `execute_sql`?
- **Relationship to the `UNMATCHED PROJECT THOUGHTS` list** — the dry-run surfaced ~19 project-category thoughts not covered by any current project definition (e.g. "Add voice dictation to second brain," "Build NAS with Raspberry Pi controller"). That's a separate, legitimate task (expanding `project_definitions.json` coverage) — don't conflate it with this pagination fix, but worth flagging as a follow-up once the underlying data is trustworthy.

---

## Related

- `mcp_improvements.md` §6 — the `get_stats` fix that surfaced this same root-cause pattern; already resolved there, now recurring here
- `wiki_implementation.md` Follow-Up Items #1 — the original (incorrect) "fix anchor topics" framing; should be corrected once this plan is scoped, cross-referencing this file
- `CURRENT.md` "Carried over from May" — same correction needed
