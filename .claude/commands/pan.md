# /pan — Panning for Gold

Extract every insight worth keeping from a YouTube video or raw text, then capture the keepers directly to your second brain.

## Input

The user provides one of:
- A YouTube URL (e.g. `https://youtu.be/FtCdYhspm7w`)
- Raw text (transcript, brain dump, meeting notes, article)

Optionally, the user may add `--commit` to skip the dry-run review and capture immediately.

## Step 0 — Fetch Transcript (YouTube URLs only)

If the input is a YouTube URL, invoke the `/transcript` skill with the URL. The transcript skill handles all machine-specific path resolution.

Read the output file it produces as the raw input for Phase 1. Tell the user the transcript was fetched and how many lines it contains.

If the transcript fetch fails (video unavailable, transcripts disabled, IP blocked), stop and tell the user.

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

**Step 1 — Overlap check:** Call `semantic_search` with the item text (limit 2). If any result has similarity ≥ 85%, show a match block directly below the item:

```
  ~ Overlap detected (92%) — "Layered agentic architecture"
    Summary: Separate memory, compute, and interface into distinct layers for independent replaceability.
    Recommendation: downgrade to ⚠️ — brain already has this principle; only keep if this source adds new nuance.
```

If no matches are above 85%, say nothing.

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

## Phase 2.5 — Draft (Always Runs)

Before any captures, draft the full text for every ✅ item (and any ⚠️ items the user confirms). Show all drafts as a numbered list so the user can review wording, request trims, or cut items before anything hits the brain.

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

After showing all drafts, ask: **"Capture these now, or any changes first?"**

If `--commit` was NOT specified (the default), stop here and wait for the user to confirm or request edits before proceeding to Phase 3.

---

## Phase 3 — Synthesize (Capture to Second Brain)

For each approved draft, call `capture_thought`:

- Set `is_external: true` whenever a URL was provided as input. Leave it unset (defaults false) for raw text with no URL.

Show the confirmation receipt for each (`✓ Captured: title [category]`).

After all captures are done, print a final summary:
```
Panning complete.
  Extracted: N items
  Captured:  N thoughts → second brain
  Skipped:   N items
```

---

## Future Enhancements

- **Update existing from overlap** — When Phase 2 overlap is detected, offer an "update existing thought" action instead of just skip/downgrade. Deferred until overlap detection workflow is proven in practice.

## Rules

- **Never summarise instead of extracting.** A summary collapses nuance. Phase 1 is extraction, not summarisation.
- **Never skip Phase 1 to go straight to capturing.** The discipline of reading every line is the point.
- **Write captures for your future self.** The thought must make sense 6 months from now without re-watching the video.
- **One thought per concept.** Don't bundle 3 insights into one capture — they won't surface independently in search.
