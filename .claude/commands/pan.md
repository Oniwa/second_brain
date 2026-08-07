# /pan — Panning for Gold

Extract every insight worth keeping from a YouTube video or raw text, then capture the keepers directly to your second brain.

## Input

The user provides one of:
- A YouTube URL (e.g. `https://youtu.be/FtCdYhspm7w`)
- Raw text (transcript, brain dump, meeting notes, article)
- Combined input (YouTube + Substack companion): The user provides a YouTube URL and separately pastes the raw Substack article text with its URL. Both cover the same topic. Treat them as a single unified source. Extract holistically across both — the written article is usually more detailed.

Optionally, the user may add `--commit` to skip the dry-run review and capture immediately.

## Step 0 — Fetch Transcript & Duplicate Pre-check

### Step 0a — Fetch Transcript (YouTube URLs only)

If the input is a YouTube URL, invoke the `/transcript` skill with the URL. The transcript skill handles all machine-specific path resolution.

Read the output file it produces as the raw input for Phase 1. Tell the user the transcript was fetched and how many lines it contains.

If the transcript fetch fails (video unavailable, transcripts disabled, IP blocked), stop and tell the user.

### Step 0b — Duplicate Pre-check (all inputs)

Before Phase 1, check whether this source has already been panned:

**If a URL was provided:** You must be able to find prior pans from *whatever* URL the user gives you. Run this lookup for **every** URL provided:

1. **Authoritative URL lookup** — Call `find_by_url` with the URL (it defaults to status `all`). This is deterministic and URL-form-agnostic: YouTube links resolve to their video ID so `youtu.be`, `watch?v=`, `?si=` tracking, `shorts`, and `embed` forms all unify; other URLs match on host+path. It returns hits **grouped by source label with counts**, flagging any source that holds active `insight` captures (the "likely already panned" signal). This replaces the old fuzzy `semantic_search`-on-the-URL-string dance — you no longer need to hand-chase companion Substack URLs, because passing *each* URL the user gave you to `find_by_url` finds them directly.
2. **Topical fallback** — After fetching the transcript (Step 0a), derive the video's core topic/title and run a `semantic_search` (or `get_context`) on that topic. This is the secondary net: it catches captures that reference the source *conceptually* but carry no URL in their `urls[]` field, which `find_by_url` structurally cannot find.

**Reading the verdict:** the strongest evidence a source is already panned is a **cluster of active `insight` captures** referencing the URL (e.g. 39 insights = unmistakably panned) — *not* the presence of a reminder. A reminder thought ("watch/pan this video") is only the to-do; conversely, a source can be fully panned with **no** reminder at all (it may have been captured directly, or its reminder already archived). So judge by the insight cluster `find_by_url` reports, and only conclude "not yet panned" when both the `find_by_url` lookup and the topical fallback come up empty.

When inspecting results, note each hit's **source label** and `is_external` status — `find_by_url` already groups by source and surfaces both.

If any results reference either URL, warn the user, grouped by source label with counts:
```
⚠️ This source may already be in your brain — found N thoughts referencing this URL:

  Source: "substack: Nate B. Jones - <label>"  (N thoughts)
    - "Thought title one"
    - "Thought title two"
    ...

Continue panning anyway, or stop here?
```

**Split-source / mislabel flag:** If the target URL appears under a source label whose title clearly describes a *different* topic than the current video/article (e.g. the URL is a YouTube video about the implementation layer, but the source label names a Substack about SaaS pricing), add this note to the warning:
```
⚠️ Note: this URL is co-labeled under a source titled "<other label>", which looks
like a different topic. The source may have been panned before but stamped with a
companion URL. Treat most of this content as already captured — pan only for
genuinely NEW insights not surfaced by the overlap checks below.
```
In this case, recommend the user continue but capture only net-new items (verified via Phase 2 overlap checks), rather than re-running a full pan.

Stop and wait for confirmation before proceeding to Phase 1.

**If raw text was provided (no URL):** Use the source label the user provides (e.g. "Q1 planning meeting", "Smith et al 2024") as the search query. If 3 or more results reference that same source label, show the same warning above.

If no matches are found, proceed silently to Phase 1.

---

## Phase 1 — Extract (No Filtering Yet)

**Rule: Read every line. Extract everything that could be valuable. Do not evaluate yet — that comes in Phase 2. When in doubt, include it.**

Go through the entire input systematically. Pull out:
- Concrete principles, rules, or frameworks stated explicitly
- Specific techniques, patterns, or methods described
- Surprising facts, stats, or counterintuitive claims
- Named tools, resources, or references mentioned
- Actionable recommendations ("you should...", "always...", "never...")
- Interesting analogies or mental models
- Warning signs or things to avoid
- Questions the content raises but doesn't fully answer

Output a numbered extraction list. Label each item with its type:
`[principle]` `[technique]` `[fact]` `[tool]` `[action]` `[model]` `[warning]` `[question]`

Example:
```
1. [principle] Separate memory, compute, and interface into distinct layers
2. [technique] Use confidence thresholds to route between cheap and expensive models
3. [tool] pgvector — Postgres extension for vector similarity search
4. [action] Always store raw input before processing so you can reprocess later
5. [warning] Don't build agent loops that can't detect when they're stuck
```

Do not skip lines because they seem obvious or repetitive. The discipline is to read everything.

---

## Phase 2 — Evaluate

For each extracted item:

**Step 1 — Overlap check:** Call `semantic_search` with the item text (limit 2). Show match blocks based on similarity band:

**Hard flag (≥ 85%)** — likely duplicate:
```
  ~ Overlap detected (92%) — "Layered agentic architecture"
    Summary: Separate memory, compute, and interface into distinct layers for independent replaceability.
    Recommendation: downgrade to ⚠️ — brain already has this principle; only keep if this source adds new nuance.
```

**Soft warning (55–84%)** — possible overlap, review before capturing:
```
  ~ Possible overlap (74%) — "Trust requires visibility into system errors"
    Summary: Systems are abandoned not for imperfection but for loss of trust from mysterious errors.
    Recommendation: review — similar concept exists; only capture if this source adds meaningfully new framing.
```

If no matches are at or above 55%, say nothing. (Floor lowered from 65% — real near-duplicate concepts, especially within a same-author/same-topic cluster, were found consistently landing at 55–64% and slipping through silently. See `pan_skill_improvements.md` §B2.)

**Step 2 — Score with reason:** Assign a score **and a one-line reason**, taking any overlap into account:

| Score | Meaning |
|-------|---------|
| ✅ Capture | Genuinely useful — actionable, insightful, or worth remembering |
| ⚠️ Maybe | Useful in context but generic or already known — capture only if novel to you |
| ❌ Skip | Noise, filler, already well-known, or too vague to be useful |

The reason must be specific — not "good insight" but *why* it's worth keeping or cutting.

Example scored list with overlap:
```
1. ✅ Capture — novel framing I haven't seen; directly applicable to current architecture

2. ~ Overlap detected (91%) — "Confidence-based model routing"
   Summary: Use a confidence threshold to decide whether to escalate from a cheap to an expensive model.
   Recommendation: downgrade to ❌ — already well-captured; no new angle here.
   ❌ Skip — already in brain with same framing; nothing new added

3. ❌ Skip — intro context, no standalone value

4. ✅ Capture — concrete technique with a named pattern, easy to act on

5. ⚠️ Maybe — solid principle but vague without surrounding context
```

After scoring, show a summary: `X items to capture, Y maybes, Z skipped.`

---

## Phase 2.5 — Merge, Draft & Trim (Always Runs)

### Step 1 — Merge check (before drafting)

Before drafting, scan the scored ✅ items (and any ⚠️ items the user confirms) against each other for items that are really one concept — the inverse of the "one thought per concept" rule: split genuinely distinct ideas, but consolidate items that only look distinct. This is an in-context comparison of the extraction list, not a new `semantic_search` call.

If any are found, state the merge explicitly before drafting, e.g.:
```
Merging items 6 and 9 into one draft — both describe the same "harness matters
more than model" point from different angles.
```
Draft once for the merged concept, not once per original item — drafting first and merging after wastes a draft and a review cycle. This is a narrated decision, not a stop-and-wait gate; it rides the single confirmation point at the end of this phase, so state it clearly enough that the user can reject the merge in their one reply.

### Step 2 — Draft

Draft the full text for every surviving ✅ item (post-merge) and any confirmed ⚠️ items. Show all drafts as a numbered list.

For each draft:
- Write it as a complete, self-contained sentence or short paragraph — not a fragment
- Include enough context that it makes sense without the source video
- Always append `Source: <Channel> - <Video Title> <url>` at the end of the text when a URL was provided — the human-readable label enables grouping by source, the URL gets extracted into the `urls[]` database field
- Keep it tight — trim filler, hedging, and re-stated context from the source

Example:
```
Draft 1: "Agentic system design principle: separate memory (Postgres/pgvector), compute
(Edge Functions/LLM calls), and interface (MCP/Discord/CLI) into distinct layers. Each
layer should be independently replaceable. Source: Nate B Jones - Why Agents Fail https://youtu.be/FtCdYhspm7w"

Draft 2: ...
```

### Step 3 — Recommended trims (proactive, after drafting)

Before asking to capture, re-read each draft for fat — restated context, editorializing, speculative asides, or filler that doesn't survive the "keep it tight" rule above — and call it out unprompted. Don't wait to be asked "any recommended trims?"; state them alongside the drafts:
```
Recommended trims:
- Draft 3: cut the closing sentence — it's inference the reader can already
  draw from the facts stated above it.
- Draft 6: cut the speculative closing clause — forecasting, not a captured fact.
```
If a draft has no fat worth cutting, say nothing about it — don't manufacture a trim to seem thorough.

### Confirm

After showing merges, drafts, and recommended trims together, ask: **"Capture these now, or any changes first?"**

If `--commit` was NOT specified (the default), stop here and wait for the user to confirm, request different trims, approve or reject a merge, or edit drafts before proceeding to Phase 3.

---

## Phase 3 — Synthesize (Capture to Second Brain)

For each approved draft, call `capture_thought` with:
- `text`: The draft text (self-contained, includes `Source:` label at end with all relevant URLs)
- `source`: `"{platform}: {Author} - {Title}"` — canonical platform; see format below
- `is_external`: `true` (always — pan is for external content by definition)

**Source field format:** `{platform}: {Author/Channel} - {Title}`

Single source examples:
```
youtube: Nate B. Jones - You're Wasting 40% Of Your AI Time On Something Fixable
substack: Nate B. Jones - Codex Plugins Matter Because the Bottleneck Moved
article: Author Name - Article Title
podcast: Show Name - Episode Title
```

Dual source (YouTube + companion Substack):
```
source field: "substack: {Author} - {Title}"  ← canonical = the written article
Both URLs appear in the capture text:
  "... Source: Author - Title <youtube_url> <substack_url>"
The urls[] field will contain both URLs for traceability.
```

Show the confirmation receipt for each (`✓ Captured: title [category]`).

After all captures are done, print a final summary:
```
Panning complete.
  Extracted: N items
  Captured:  N thoughts → second brain
  Skipped:   N items
```

---

## Phase 4 — Archive the "to pan" Reminder (Always Runs)

A pan is not finished until its to-do is cleared. After Phase 3 — **and also whenever the duplicate pre-check reveals the source was already fully panned** (i.e. even if you capture nothing new) — locate and archive the reminder thought that asked you to pan this source, if one exists.

1. From the Step 0b lookups you already ran, identify the reminder-style thought for this source — a short "watch/pan this video", "review & extract insights", "pan for gold" thought whose `URLs:` line contains the provided URL.
2. If one exists, call `archive_thought` with its ID so it stops showing up as an open pan.
3. Confirm to the user: `✓ Archived reminder: "<title>" (<id>)`. If no reminder thought exists, say so and move on — do not fabricate one.
4. If the user keeps an external open-pans tracker (e.g. `open_pans.md`), check the corresponding item off there too.

Only archive genuine reminder/to-do thoughts — never archive the captured insight thoughts themselves.

---

## Future Enhancements

- **Update existing from overlap** — When Phase 2 overlap is detected, offer an "update existing thought" action instead of just skip/downgrade. Deferred until overlap detection workflow is proven in practice.

## Rules

- **Never summarise instead of extracting.** A summary collapses nuance. Phase 1 is extraction, not summarisation.
- **Never skip Phase 1 to go straight to capturing.** The discipline of reading every line is the point.
- **Write captures for your future self.** The thought must make sense 6 months from now without re-watching the video.
- **One thought per concept.** Don't bundle 3 insights into one capture — they won't surface independently in search.
