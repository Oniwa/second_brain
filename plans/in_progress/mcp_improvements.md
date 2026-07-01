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

**Fix:** Add a deterministic exact/substring lookup on the `urls[]` field so a single call reliably returns every thought referencing a URL.

**Possible interface:**
```
find_by_url(url: string, status?: active|archived|all) → thoughts whose urls[] contains url
```
Implementation: DB-level `WHERE urls @> ARRAY[url]` for exact match, or `ILIKE '%<videoID>%'` across the `urls[]` field to tolerate tracking-param differences (`?si=`, `?is=`) and youtu.be vs youtube.com/watch forms. Normalize/canonicalize URLs (strip query params, unify host) before matching.

**Downstream:** Once available, simplify `/pan` Step 0b to call `find_by_url` first as the authoritative dedup check, keeping the topical fallback only as a secondary net.

**Phase:** 4 (higher priority — fixes an active, recurring correctness bug in pan dedup)
