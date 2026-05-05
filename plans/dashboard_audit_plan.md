# Dashboard Audit Page Plan

## What It Does

A dedicated action item triage page at `dashboard/audit.html`. Shows every active thought with outstanding action items, oldest first. Each row has an archive button with an optional completion note. Phase 2 adds inline `raw_text` editing with full resynthesis.

Separate page (not a tab) — different workflow from the analytics dashboard. Dedicated URL, fast load, focused fetch. Both pages share a left sidebar nav.

---

## Goals & Success Criteria

- All active thoughts with non-empty `action_items[]` are surfaced, oldest first
- Count header: "N thoughts with outstanding action items"
- Archiving with no reason: flips `status = 'archived'` only — identical to MCP `archive_thought`
- Archiving with a reason: appends `\nCompleted {YYYY-MM-DD}: {reason}` to `raw_text`, updates `content_hash`, flips `status = 'archived'` — all in one atomic PATCH
- Archived thoughts stop appearing in digests immediately (digest filters by `status = 'active'` — confirmed)
- Empty state handled: "No active thoughts with action items"
- Both dashboard pages share a left sidebar nav with text labels (Dashboard, Audit)
- Page works without any build step — plain HTML, no framework

---

## Scope

### In Scope (Phase 1)
- `dashboard/audit.html` — new file with sidebar nav, count header, thought cards, archive action
- `dashboard/shared.css` — shared styles + sidebar layout; extracted from `index.html`
- `dashboard/index.html` — refactored to use sidebar nav + link `shared.css`
- Archive with reason: re-fetch `raw_text` immediately before PATCH (Option A), append annotation, compute `content_hash` via Web Crypto SHA-256 (native browser API, no dependency), PATCH atomically
- Archive without reason: PATCH `status` only — no `raw_text` change, no rehash
- `raw_text` always visible on each card (no toggle, no collapse)
- Inline feedback per row: button disabled while in-flight, row fades out on success, inline error on failure

### In Scope (Phase 2 — blocked on Edge Function update mode)
- Inline `raw_text` edit textarea per row
- Submit → Edge Function update mode → row refreshes with new title/summary/topics
- Cancel button to discard edit without saving
- Phase 2 is blocked until `process-thought` Edge Function supports `id` param (update mode)

### Out of Scope
- Pagination (action item backlog should be manageable; fetch all at once)
- Editing fields other than `raw_text`
- Per-item action item completion (archive when all done; use MCP `update_thought` for surgical edits)
- Bulk archive
- Sorting controls (oldest-first is always correct for triage)
- Sidebar icons (deferred until sidebar gets collapse/shrink toggle)

---

## Architecture

**Keys:** Both anon key (read) and service role key (write) present in the file. Acceptable — `audit.html` is local-only, never web-accessible. Web-accessible migration to FastAPI + Jinja2 is the future trigger.

**Fetch strategy:** Single query on page load — `GET /rest/v1/thoughts` filtered to `status=eq.active`, ordered `created_at.asc`, select only needed columns. Filter `action_items` client-side for `length > 0`.

**Archive (no reason):** PATCH `status = 'archived'` only. Identical to MCP `archive_thought`. No `raw_text` change, no hash update.

**Archive (with reason):**
1. Re-fetch `raw_text` immediately before PATCH
2. Append `\nCompleted {date}: {reason}` to current `raw_text`
3. Compute new `content_hash` via Web Crypto: `normalizeText(newRawText)` → SHA-256 → hex lowercase
4. PATCH: `{ status: 'archived', raw_text: newRawText, content_hash: newHash }` atomically

**Hash normalization (must match Edge Function):** `text.toLowerCase().trim().replace(/\s+/g, ' ')`

**Sidebar layout:** Both pages use `.layout` (flex row) → `.sidebar` (200px fixed) + `.main` (flex-grow). Text labels only. `index.html` is Dashboard (active link), `audit.html` is Audit (active link).

**Phase 2 edit:** POST to `process-thought` Edge Function with `{id, raw_text}`. Edge Function re-embeds, re-classifies, patches the existing row (preserving status). Row refreshes from response.

---

## Row Layout (Phase 1)

```
┌─────────────────────────────────────────────────────┐
│ Title                              [category badge]  │
│ May 1, 2026 · mcp                                    │
│                                                      │
│ Summary text                                         │
│                                                      │
│ RAW TEXT                                             │
│ ┌─────────────────────────────────────────────────┐ │
│ │ raw_text content (always visible, read-only)    │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ ACTION ITEMS                                         │
│   • item one                                         │
│   • item two                                         │
│                                                      │
│ [Phase 2: raw_text textarea — hidden until Edit]     │
│ ─────────────────────────────────────────────────── │
│ Completion note: [________________]  [Archive]       │
└─────────────────────────────────────────────────────┘
```

---

## Shared CSS (`dashboard/shared.css`)

Extracted from `dashboard/index.html`:
- CSS reset
- CSS custom properties (`--bg`, `--surface`, `--border`, `--text`, `--muted`, `--secondary`, `--accent`)
- `body` base styles (background, color, font-family)
- `.layout` / `.sidebar` / `.sidebar-title` / `.sidebar nav a` / `.main`
- `.stat-card` (used by both pages)
- `.error-banner` (replaces `#error` style)

Both pages link this file. Page-specific styles remain inline.

---

## Supabase Query

```js
GET /rest/v1/thoughts
  ?status=eq.active
  &order=created_at.asc
  &select=id,title,summary,raw_text,category,action_items,source,created_at
  &limit=500
```

Filter client-side: `thoughts.filter(t => t.action_items && t.action_items.length > 0)`

---

## Archive PATCH

**No reason:**
```js
{ status: 'archived' }
```

**With reason:**
```js
{
  status: 'archived',
  raw_text: `${refetchedRawText}\nCompleted ${date}: ${reason}`,
  content_hash: await hashText(newRawText)   // Web Crypto SHA-256
}
```

Headers: `apikey: SERVICE_ROLE_KEY`, `Authorization: Bearer SERVICE_ROLE_KEY`, `Prefer: return=minimal`

---

## Error Handling

- Fetch failure on load: show `.error-banner`, log to console
- Re-fetch failure before archive: inline error, button re-enabled
- Archive PATCH failure: inline error below row, button re-enabled, row stays visible
- Phase 2 edit failure: inline error, textarea stays open with edits intact

---

## Files to Create / Modify

| File | Action |
|---|---|
| `dashboard/shared.css` | CREATE — shared styles + sidebar layout |
| `dashboard/audit.html` | CREATE — Phase 1 |
| `dashboard/index.html` | MODIFY — add sidebar nav, link `shared.css`, remove extracted styles |
| `supabase/functions/process-thought/index.ts` | MODIFY — Phase 2 only |

---

## Key Decisions

| Decision | Choice | Reason |
|---|---|---|
| Tab vs. separate page | Separate page (`audit.html`) | Different workflow; dedicated URL |
| Navigation | Left sidebar, text labels | Scalable; icons deferred to collapse-toggle feature |
| Default landing page | `index.html` (analytics dashboard) | Browse first, triage on demand |
| Service role key in HTML | Accepted | Local-only; web-accessible migration is the trigger |
| Filter action_items | Client-side | Avoids array filter syntax; dataset is small |
| Sort order | `created_at ASC` (oldest first) | Triage order |
| Archive (no reason) | Status flip only | Parity with MCP `archive_thought` |
| Archive (with reason) | Append to raw_text + rehash + archive atomically | Mirrors CLI update-then-archive workflow |
| Hash in browser | Web Crypto SHA-256 (native, no dependency) | Maintains `content_hash` integrity |
| Re-fetch before PATCH | Yes (Option A) | Guards against stale raw_text overwrite |
| raw_text display | Always visible, no toggle | Toggle deferred if user finds it noisy |
| Per-item completion | Out of scope | Archive = done; MCP handles surgical edits |
| Digest filtering | Already confirmed | `generate-digest` line 176: `eq("status", "active")` |

---

## Order of Operations

### Phase 1
1. Create `dashboard/shared.css`
2. Refactor `dashboard/index.html` — add sidebar, link `shared.css`, remove extracted styles
3. Create `dashboard/audit.html` — fetch, render, archive
4. Test: load audit page, verify count header, archive a thought, confirm it disappears and is archived in DB

### Phase 2 (after Edge Function update mode is implemented)
5. Add edit textarea (hidden by default) to each card
6. Wire `[Edit]` button to expand textarea
7. Wire `[Save]` to POST Edge Function, refresh card from response
8. Wire `[Cancel]` to collapse textarea, discard changes
