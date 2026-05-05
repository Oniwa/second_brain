# /pan — Panning for Gold

Extract every insight worth keeping from a YouTube video or raw text, then capture the keepers directly to your second brain.

## Input

The user provides one of:
- A YouTube URL (e.g. `https://youtu.be/FtCdYhspm7w`)
- Raw text (transcript, brain dump, meeting notes, article)

Optionally, the user may add `--dry-run` to preview all captures without writing anything to the brain.

## Step 0 — Fetch Transcript (YouTube URLs only)

If the input is a YouTube URL, run the transcript tool first:

```bash
cd /home/oniwa/PycharmProjects/youtube_transcript && \
  .venv/bin/python main.py <URL> --output /tmp/pan_transcript.txt
```

Then read `/tmp/pan_transcript.txt` as the raw input for Phase 1. Tell the user the transcript was fetched and how many lines it contains.

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

For each extracted item, assign a score:

| Score | Meaning |
|-------|---------|
| ✅ Capture | Genuinely useful — actionable, insightful, or worth remembering |
| ⚠️ Maybe | Useful in context but generic or already known — capture only if novel to you |
| ❌ Skip | Noise, filler, already well-known, or too vague to be useful |

Show the scored list. Be ruthless — most items from a good video should score ✅ or ⚠️, but intro/outro fluff, obvious statements, and pure context should be ❌.

After scoring, show a summary: `X items to capture, Y maybes, Z skipped.`

Ask the user: **"Capture all ✅ items now? Or review the list first?"**

---

## Phase 3 — Synthesize (Capture to Second Brain)

If `--dry-run` was specified, skip all `capture_thought` calls and instead print each thought as it would be captured — formatted exactly as it would appear in the brain — then print the final summary with `[DRY RUN — nothing captured]`. This lets the user review and tune before committing.

For each ✅ item (and any ⚠️ items the user confirms), call `capture_thought` with a well-formed thought:

- Write it as a complete, self-contained sentence or short paragraph — not a fragment
- Include enough context that it makes sense without the source video
- Add the source URL if one was provided
- Tag with relevant topics so it surfaces in future searches

Example capture for item 1 above:
> "Agentic system design principle: separate memory (Postgres/pgvector), compute (Edge Functions/LLM calls), and interface (MCP/Discord/CLI) into distinct layers. Each layer should be independently replaceable. Source: https://youtu.be/FtCdYhspm7w"

Capture each item one at a time using the `capture_thought` MCP tool. Show the confirmation receipt for each (`✓ Captured: title [category]`).

After all captures are done, print a final summary:
```
Panning complete.
  Extracted: N items
  Captured:  N thoughts → second brain
  Skipped:   N items
```

---

## Future Enhancements

- **Conflict detection (Phase 2.5)** — Before capturing each ✅ item, run `semantic_search` to find existing thoughts with >80% similarity. Surface conflicts side-by-side and ask: confirm conflict (capture with `contradicts` tag + old ID), update existing thought, or skip. Adds 1 MCP call per item but prevents silent contradictions accumulating in the brain.

## Rules

- **Never summarise instead of extracting.** A summary collapses nuance. Phase 1 is extraction, not summarisation.
- **Never skip Phase 1 to go straight to capturing.** The discipline of reading every line is the point.
- **Write captures for your future self.** The thought must make sense 6 months from now without re-watching the video.
- **One thought per concept.** Don't bundle 3 insights into one capture — they won't surface independently in search.
