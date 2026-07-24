# MCP Server Improvements

Improvements surfaced from reviewing Karpathy's LLM wiki approach (Dream Labs AI video).

---

## 1. Knowledge Gap Detection Tool (`get_gaps`)

A dedicated MCP tool that takes stated goals from the brain and recent captures, then asks Claude what's missing — what knowledge, decisions, or actions are implied by the goals but absent from the brain.

Distinct from `get_context` (which retrieves relevant thoughts) — this is inferential: it surfaces what *isn't* there rather than what is.

**Possible interface:**
```
get_gaps(topic?: string) → list of identified gaps relative to goals
```

**Phase:** 5

---

## 2. Skill/Persona Thought Category

A new thought type designed not to surface in semantic search results but to *influence* AI responses. A `skill` thought would contain a distilled perspective from an expert or framework (e.g., "Hormozi business lens", "Karpathy system design principles"). Active skill thoughts would be injected into every `get_context` response.

Requires:
- Schema change: new `type` value (`skill`) in the thoughts table
- MCP update: `get_context` includes all active skill thoughts in its response payload
- New tool or flag on `capture_thought` to mark a thought as a skill

**Phase:** 5

---

## 3. Audit History Surfacing in `get_context`

Review whether `get_context` and `meeting_prep` are leveraging the full capture history (timestamps, source patterns, recency) to produce compounding, personalized context — or just doing point-in-time semantic retrieval.

Karpathy's log.md mechanism works because the AI reads the *history of interactions*, not just stored facts. Check if our equivalent (timestamped thought captures) is being used as effectively as possible in context assembly.

**Phase:** 4–5 (review task, may surface as a quick win)

---

## 4. Exact URL Lookup Tool (`find_by_url`)

**Problem (proven 2026-07-01):** We capture every source URL in each thought's `urls[]` field, but no tool can *retrieve* a thought by its URL. `semantic_search` is embedding-only — it matches on meaning, and a URL string carries no semantic meaning. As a result:
- Searching a video URL (or bare video ID) ranks the short "watch/pan this" *reminder* at the top and never surfaces the actual captured insights, because the reminder's embedding is dominated by the URL while the real captures' embeddings are dominated by their concepts.
- `get_context` rejects URL-only queries outright (`"text required"`).

This is the root cause of the recurring pan-dedup blind spot: sources that were already fully panned (jwtpMSRAPAQ, ltbzgzZZmgI, l8BloTSLK6M, n0nC1kmztSk, UsCgEuIAclE) all initially looked "unpanned" on a URL search. The `/pan` skill currently works around this with a 3-part lookup (direct URL → follow reminder's companion URL → topical fallback), but that's fuzzy and depends on guessing the topic.

**Fix:** Add a deterministic substring lookup on the `urls[]` field so a single call reliably returns every thought referencing a URL, tolerant of the URL-form heterogeneity that actually exists in the corpus.

---

### Resolved design (grilled 2026-07-24)

Grounded against the live DB: `urls[]` stores URLs **raw, exactly as extracted** (no canonicalization at capture, see `process-thought/index.ts` `extractUrls`). The same video therefore lives under `youtu.be/<id>`, `youtube.com/watch?v=<id>`, and forms with `?si=` tracking params. That heterogeneity — not the absence of a lookup — is the real failure mode, so a plain exact `@>` match would silently reproduce the dedup blind spot. Corpus at grill time: 1,300 YouTube / 544 Substack / rest a long tail of blogs; max any single video ID appears is 39 rows.

**Signature:** `find_by_url(url: string, status?: active|archived|all, limit?: number)` → thoughts referencing the URL, grouped by source.

**1. Matching — canonicalize in TS, match in SQL.**
- **YouTube** (`youtube.com`/`youtu.be`): extract the 11-char video ID (from the `v=` param or the `youtu.be/<id>` path), match `%<id>%`. Unifies `youtu.be` ↔ `watch?v=` ↔ `?si=` variants — the actual bug.
- **Everything else** (Substack, blogs — identity lives in the **path**): lowercase host, strip scheme + `www.` + query string + fragment, match `%<host+path>%`. Query strings (`?utm_*`, Substack `?r=`, `?si=`) are pure tracking noise. Corpus confirms non-YouTube URLs are path-identified and stored clean (e.g. `natesnewsletter.substack.com/p/<slug>`).
- **YouTube is the one special case** precisely because it's the only major source that puts identity in the query string rather than the path.

**2. Input — accept three shapes.**
- Full URL (either YouTube form) · bare 11-char ID (`^[A-Za-z0-9_-]{11}$` → treat as a YouTube ID directly) · bare `host/path` · else fall back to treating the raw string as a literal substring key.
- **Min-length guard:** resulting match key < ~4 chars → return `"query too broad"` rather than substring-scanning the whole table.
- **Bare-domain input** (e.g. `natesnewsletter.substack.com`) intentionally matches **every** thought from that host — kept as a feature ("everything from this source"), bounded by `limit` + pagination.

**3. Query architecture — filter server-side.**
- New SQL RPC filters in the DB: `WHERE EXISTS (SELECT 1 FROM unnest(t.urls) e WHERE e ILIKE '%' || key || '%')`, returning only matches. TS does the canonicalization and passes a clean key; SQL does the match. Keeps URL-parsing in readable TypeScript, not gnarly `regexp_replace`.
- **Sequential scan accepted** (no new index): the existing `thoughts_urls_gin` (migration 002) serves only array containment `@>`, not `ILIKE` over `unnest(urls)`. At ~1,856 rows a seq scan is sub-millisecond; a trigram index is unwarranted at this size. Note in migration.
- **`limit` default 100, internal paginate-to-exhaustion** using the proven `compile_wiki.py:274` `_fetch_all` offset/limit pattern (`POSTGREST_PAGE_SIZE = 1000` + safety cap), ported to TS — this is the codebase's *first* TS pagination loop (the `getStats` fix sidestepped pagination via count-only queries). Only the bare-domain case ever needs more than one page today.

**4. Status default = `all`** (not `active` like the other tools).
- A URL match is already narrow and unambiguous, so there's no noise cost to showing everything. More importantly, the only row that ever gets archived is the **retired reminder** (`pan.md:246` forbids archiving insight thoughts) — and an archived reminder is the single cleanest "already panned *and closed*" signal in the system. Defaulting to `active` would hide exactly that, losing the distinction between "never queued" and "queued and completed."

**5. Output.** Same row shape as `list_recent`/`get_needs_review` (`id, title, source, status, category, is_external, created_at` + the matched `urls[]` line), sorted by source label then recency, led by a `**N thought(s) across M source(s) reference <canonical-key>**` header so the dedup verdict is readable at a glance. Serves `/pan` Step 0b's group-by-source-with-counts need directly (`pan.md:36-40`).

**6. Downstream — rewire `/pan` Step 0b in this same change.**
- Replace **part 1** (direct URL `semantic_search`) → a single `find_by_url` call per provided URL. Run it on *every* URL the user supplies.
- **Retire part 2** (follow-the-companion-URL hop) — it was a workaround for exact-match blindness; with ID/path canonicalization, both the video URL and its companion Substack URL are directly findable by passing each to `find_by_url`.
- **Keep part 3** (topical fallback) as the secondary net — it catches thoughts that reference a source *conceptually* without carrying its URL, which `find_by_url` structurally cannot find.
- **Verdict update:** treat a **cluster of active `insight` captures** as "already panned," not just a retired reminder. Proven during the grill: `iUSdS-6uwr4` has **39 active insights and 0 reminder** — it was panned directly with no reminder ever created, so "an archived reminder exists" is *not* a reliable dedup signal on its own.

**Files to change:**
| File | Action |
|------|--------|
| `supabase/migrations/009_find_by_url.sql` | NEW — RPC that canonical-key-filters `urls[]` server-side (seq scan, documented) |
| `mcp/src/server.ts` | MODIFY — `find_by_url` tool: TS canonicalizer (YT ID / host+path), min-length guard, internal paginate-to-exhaustion, grouped output |
| `.claude/commands/pan.md` | MODIFY — Step 0b rewrite (part 1 → `find_by_url`, retire part 2, keep part 3, insight-cluster verdict) |

**Phase:** 4 (higher priority — fixes an active, recurring correctness bug in pan dedup)

---

## 5. Pan Queue Visibility (Discord-captured videos as a first-class queue)

**Problem (proven 2026-07-01):** One of the primary uses of the Discord `#sb-inbox` is capturing YouTube videos to "pan for gold." But every Discord message — pan requests, stray thoughts, meeting notes — lands in one undifferentiated `thoughts` bucket with `source=discord`. A "pan this video" is a *task with a lifecycle* (submitted → panned → archived), yet it is stored identically to a knowledge insight. The only retrieval surfaces are `semantic_search` (matches meaning — blind to URLs and to "this is a to-do") and `list_recent` (hard-capped at 50, no pagination/date-exact filter). Result: pan reminders silently pile up and get lost. On 2026-07-01, 11 pan submissions since 6/18 were invisible to every MCP tool; only a direct PostgREST query (`source=eq.discord&created_at=gte.…`) surfaced the ground truth, and `open_pans.md` had drifted out of sync (missing 9 of them).

The reliable primitive already exists (a `source=discord` + YouTube-URL + `status=active` query returns the exact set); it just is not wired into any surface the user actually looks at. Archiving the reminder already serves as the "done" signal.

**Fixes, ranked by leverage ÷ effort:**

1. **First-class pan type at capture time** *(structural root fix)* — In `process-thought`/`discord/bot.py`, when a Discord message has a YouTube URL + pan intent ("pan/review this video for gold"), tag it `category=pan_queue` (or add a `pan_status: open` field). Turns an invisible thought into a queryable queue item, robust even for CLI-submitted or oddly-worded pans. Requires a small classification-prompt/schema tweak.
2. **`brain.py --pending-pans` + Discord `!pans` command** — ✅ **`--pending-pans` shipped 2026-07-11** as part of `get_pans_skill.md` (see Update below); the Discord `!pans` half is not built. Reliable primitive; overlaps with `find_by_url` (#4) infrastructure.
3. **Dedicated "🎬 Open pans (N)" section in the daily/weekly digest** *(passive recurring visibility)* — The digest (`generate-digest` edge fn + `discord/digest.py`) already lands in Discord DM + Gmail. Add a section listing open pans and the oldest age. They can't rot unseen if every digest shows the backlog.
4. **Pan-aware nudge** *(escalation)* — Extend `scripts/nudge.py`: if open pans exceed N or age past a threshold, DM "9 videos waiting to pan, oldest 13 days." Turns silence into an actionable backlog alert.
5. **Auto-generate `open_pans.md`** — ✅ **Shipped 2026-07-11**, superseded by the `get_pans` skill (see Update below) rather than a bare `brain.py --sync-pans` flag.

**Recommended sequencing:** ~~#2 first~~ done; #1 + #3 remain as the durable fix, with #4 as a cheap add-on once the query helper exists (it already does, via `--pending-pans`).

**Relationship to #4:** Both stem from the same root — URLs and task-state are not first-class in retrieval. `find_by_url` (#4) fixes *dedup lookups*; this item fixes *backlog enumeration/visibility*. They can share a canonical-URL normalization helper and the same PostgREST query layer.

**Phase:** 4 (item #2 ✅ shipped; #1/#3 still durable/open)

**Update 2026-07-11 — resolved and shipped.** Items #2 and #5 were built together as the `get_pans` skill (`.claude/commands/get_pans.md`, Haiku-driven, `disable-model-invocation: true`) plus `scripts/brain.py --pending-pans` as its deterministic backend — see `plans/done/get_pans_skill.md`. Confirmed during implementation: `get_pans` fully supersedes item #5's original `--sync-pans` idea (same feature, built as a skill instead of a bare flag); item #2's structural query is exactly `--pending-pans`, though the Discord `!pans` half of item #2 was not built. Ground-truthed against the live DB (19 open pans, verified exact match) before shipping. Items #1 (first-class `pan_status` at capture time) and #3 (digest section) remain open.

---

## 6. `get_stats` All-Time Counts Are Capped at 1000 (bug) — ✅ Fixed 2026-07-03

**Problem (proven 2026-07-02):** `get_stats` reports `Total: 1000, active: 1000, archived: 0` — a suspiciously round number and a flat-wrong `archived: 0` (191 thoughts are actually archived). Direct PostgREST exact counts give the truth: **1,840 total / 1,649 active / 191 archived**.

**Root cause:** `getStats` (`mcp/src/server.ts` ~line 151) does:
```ts
supabase.from("thoughts").select("status")   // fetch all rows, tally in JS
```
It pulls every row and counts statuses client-side, but the Supabase/PostgREST client enforces a **default `max-rows` of 1000**, so it silently receives only the first 1000 rows and counts those. Any brain with >1000 thoughts gets truncated, wrong all-time totals and a bogus `archived` count. The 30-day *window* section is unaffected only because it currently sits under 1000.

**Why it matters:** every judgment about the brain's health (growth, archival hygiene, category mix) runs on a lying gauge. "Instrument before you optimize" — this should be fixed before trusting any stats-driven decision.

**Fix:** replace the row-fetch-and-tally with count-only queries — one HEAD request per status plus a total:
```ts
supabase.from("thoughts").select("*", { count: "exact", head: true })                     // total
supabase.from("thoughts").select("*", { count: "exact", head: true }).eq("status", "active")
// ...archived, needs_review
```
`head: true` returns no rows (just the `Content-Range` count), so it's cheap and cap-immune. The 30-day window breakdown can keep fetching rows (it needs category/topic detail) but should also switch to a count query for its totals to stay correct past 1000.

**Phase:** 4 (quick, high-value — unblocks honest measurement)

---

**Resolution (2026-07-03):** Implemented in `mcp/src/server.ts` `getStats()` as 4 explicit named `count: "exact", head: true` queries (total, active, archived, needs_review) run in parallel alongside the windowed row-fetch — total is its own independent unfiltered count, not derived by summing the three statuses. Each query fails fast with a distinct error message identifying which count failed. Added a drift warning (`⚠ N thought(s) with an unrecognized status`) that fires if total ever doesn't equal active+archived+needs_review — possible in theory since `status` has no `NOT NULL` constraint (`001_init.sql:17`), though never observed in practice. The windowed section was deliberately left untouched (it's ~640 rows/30 days today, nowhere near the cap) but got a one-line comment noting it has the same theoretical row-cap risk if capture volume ever spikes.

Verified against `execute_sql` ground truth: **1856 total / 1665 active / 191 archived / 0 needs_review** (matches exactly, no drift). Note the real numbers had grown since this bug was first proven on 2026-07-02 (1,840/1,649/191 then) — the brain gained thoughts in the interim, as expected.
