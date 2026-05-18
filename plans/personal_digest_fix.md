# Digest Action Items — Filter External Captures

## Context

The daily digest "Top 3 actions" section surfaces action items extracted from panned external articles (YouTube videos, Substack posts) alongside personal to-dos. Because `process-thought` runs Claude classification on every capture including external ones, panned thoughts get AI-extracted action items like "Apply these five tests when installing Codex plugins" — which then appear in the digest as if they're personal tasks. The user doesn't want to act on other people's recommended actions; they want the digest to surface things they personally need to do.

The `is_external` boolean field already exists on the `thoughts` table (migration 006, backfill applied) and is set correctly for panned captures. The fix is to use it.

**Note:** The wiki plan lives in `plans/wiki_implementation.md` in the repo — not lost by overwriting this file.

---

## Root Cause

`generate-digest/index.ts` fetches all active thoughts and passes them to Claude. `formatThoughts()` includes the `Actions:` line for every thought regardless of `is_external`. Claude then picks the top 3 actions from the full pool, often choosing action items from external captures because they're specific and actionable-sounding.

---

## Fix: Three-Part Change to `supabase/functions/generate-digest/index.ts`

### Part 1 — Add `is_external` to query + interface

**Lines 73-82** — Add `is_external` to the `Thought` interface:
```typescript
interface Thought {
  title: string;
  summary: string;
  category: string;
  action_items: string[];
  people: string[];
  topics: string[];
  created_at: string;
  source: string;
  is_external: boolean;   // ADD
}
```

**Line 175** — Add `is_external` to the main thoughts `.select()`:
```typescript
.select("title, summary, category, action_items, people, topics, created_at, source, is_external")
```

**Line 200** — Same addition to the archived thoughts `.select()`.

### Part 2 — Tag thoughts in formatThoughts + suppress external action items

**Lines 84-99** — Update `formatThoughts`:
```typescript
function formatThoughts(thoughts: Thought[]): string {
  return thoughts.map((t, i) => {
    const age = Math.floor(
      (Date.now() - new Date(t.created_at).getTime()) / (1000 * 60 * 60 * 24)
    );
    const tag = t.is_external ? "[EXTERNAL]" : "[PERSONAL]";
    const lines = [
      `${i + 1}. [${t.category}] ${t.title} ${tag}`,
      `   Summary: ${t.summary}`,
      (!t.is_external && t.action_items.length) ? `   Actions: ${t.action_items.join(" | ")}` : "",
      t.people.length ? `   People: ${t.people.join(", ")}` : "",
      t.topics.length ? `   Topics: ${t.topics.join(", ")}` : "",
      `   Captured: ${age} day(s) ago via ${t.source}`,
    ];
    return lines.filter(Boolean).join("\n");
  }).join("\n\n");
}
```

Two effects: every thought gets a `[PERSONAL]` or `[EXTERNAL]` tag visible to Claude, and external thoughts have their `Actions:` line stripped so Claude cannot pick from them.

### Part 3 — Update all three prompts

Add this sentence immediately before the closing word-count instruction in `DAILY_PROMPT`, `WEEKLY_PROMPT`, and `WEEKLY_REVIEW_PROMPT`:

```
For "Top 3 actions" and "One thing that's been sitting": only draw from [PERSONAL] thoughts. [EXTERNAL] thoughts are insights from other people's content — use them only to inform themes and patterns, never as personal to-dos.
```

---

---

## Pan Skill Fixes: `.claude/commands/pan.md`

### Fix 1 — Always set `is_external: true` in pan (line 154)

**Current (wrong):**
> Set `is_external: true` whenever a URL was provided as input. Leave it unset (defaults false) for raw text with no URL.

**Replace with:**
> Always set `is_external: true`. The /pan skill is for external content by definition — other people's videos, articles, transcripts. If you're capturing your own original thoughts, use `capture_thought` directly, not /pan.

**Why:** Today's 21 Substack captures were panned from pasted article text (not a bare URL input), so `is_external` was never set. Those captures are now polluting the digest action items. The URL-vs-text distinction is the wrong signal — the right signal is the skill itself.

### Fix 2 — Standardize `source` field format + handle dual-source inputs

The user frequently pans a YouTube video AND the companion Substack article together (same content, different formats). The skill needs explicit guidance for this pattern.

**Source field format — add to Phase 3:**

```
Source field format: `{platform}: {Author/Channel} - {Title}`

Single source examples:
  youtube: Nate B. Jones - You're Wasting 40% Of Your AI Time On Something Fixable
  substack: Nate B. Jones - Codex Plugins Matter Because the Bottleneck Moved
  article: Author Name - Article Title
  podcast: Show Name - Episode Title

Dual source (YouTube + companion Substack):
  source field: "substack: {Author} - {Title}"  ← canonical = the written article
  Both URLs appear in the capture text:
    "... Source: Author - Title <youtube_url> <substack_url>"
  The urls[] field will contain both URLs for traceability.
```

**Step 0 — update Input section and duplicate pre-check for dual-source pattern:**

Add to the Input section:
```
Combined input (YouTube + Substack companion):
  The user provides a YouTube URL and separately pastes the raw Substack article text
  with its URL. Both cover the same topic. Treat them as a single unified source.
  Extract holistically across both — the written article is usually more detailed.
```

Update Step 0b duplicate pre-check:
```
If both a YouTube URL and a Substack URL are provided, run semantic_search against
BOTH URLs separately. If either was already panned, show the warning and stop.
```

### Fix 3 — Explicit capture_thought template in Phase 3

Replace the current vague Phase 3 instruction with an explicit call template:

```
For each approved draft, call capture_thought with:
  text:        The draft text (self-contained, includes Source: label at end with all relevant URLs)
  source:      "{platform}: {Author} - {Title}"  (canonical platform; see format above)
  is_external: true  (always — pan is for external content)
```

---

## Files to Modify

| File | Change |
|---|---|
| `supabase/functions/generate-digest/index.ts` | Parts 1–3 above (query, formatThoughts, prompts) |
| `.claude/commands/pan.md` | Fix is_external rule, add source format template, explicit capture template |

Deploy after editing index.ts: `supabase functions deploy generate-digest`

---

## Verification

1. Trigger a manual digest: `python discord/digest.py daily`
2. Confirm "Top 3 actions" contains only personal captures — nothing from recent panned articles
3. Confirm "One thing that's been sitting" is a personal thought
4. Confirm weekly "Pattern noticed" still references external themes (they're still in context)
5. After next pan session, confirm `is_external = true` on all captured thoughts regardless of input format
6. After next pan session, confirm `source` field follows `{platform}: Author - Title` format
