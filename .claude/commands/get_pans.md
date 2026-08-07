---
name: get_pans
description: Regenerate open_pans.md from the second brain's actual open "pan for gold" backlog. Use when the tracker looks stale or before a pan session to see what's actually pending.
model: claude-haiku-4-5-20251001
disable-model-invocation: true
---

Regenerate `open_pans.md` from the live second brain — replaces the old manual reconciliation process.

See `plans/done/get_pans_skill.md` for the full design and reasoning behind every decision below. Do not re-derive or second-guess these — they were resolved deliberately via grill-me and confirmed against a hand-verified ground truth.

## Step 1 — Fetch candidates

Run:
```
python scripts/brain.py --pending-pans
```

This returns the complete, correct candidate set as JSON — every `source=discord`, `status=active` thought with at least one URL. **This is the full answer already; do not filter it further.** Do not exclude items because they don't explicitly say "pan" or "gold," and do not try to judge whether something "sounds like" a real pan request — a prior attempt at that kind of filtering was wrong on review (it excluded legitimate candidates, including two that actually did say "pan it for gold" later in the text). Any saved-but-unreviewed URL belongs in the list.

## Step 2 — Extract a due date per item, if stated

For each candidate's `raw_text`, look for a stated due date or relative due phrase (e.g. "due end of June," "do it by July 10th," "due next week"). This requires judgment — dates are free text, not a structured field, and may be relative to the item's `created_at`.

- If a due date/phrase is found, keep the **original phrasing** for display (don't over-normalize what's shown to the user) but also resolve it to an actual date for sorting, using `created_at` as the reference point for relative phrases.
- If no due date is stated, the item has no due date — that's expected and fine, not an error.

## Step 3 — Sort

- Items **with** a resolved due date first, ascending (soonest due first).
- Items **without** a due date after, ordered by `created_at` ascending (oldest capture first).

## Step 4 — Write `open_pans.md`

Format, one line per item:
```
- [ ] <url> — <short topic description, ~5-10 words, the "title" field from Step 1's JSON> (saved <created_at date>, due <original due phrase, if any>) — `<thought id>`
```

Full file structure:
```
# Open Pans

Sources saved to the second brain to "pan for gold" but not yet processed. Check off each item once it has been panned and captured — or just re-run `/get_pans` afterward and it'll drop off automatically.

_Last synced from database: <today's date> (via `brain.py --pending-pans`)_

## Open pans

<one line per item, per the format above>
```

If there are zero candidates, still write a valid file with an empty "Open pans" section and a line noting "No open pans right now."

**This is a full, clean overwrite — not a merge.** Do not read the existing `open_pans.md` first or try to preserve any of its current content (closed-out entries, old section groupings, prior annotations). The database and git history are the durable record; this file is a disposable, regenerated view of what's currently open. See Decision 1 in the plan for why this is deliberate, not an oversight.

**Write with `newline="\n"` explicitly** (or equivalent) — this file is git-tracked and edited from both a Linux and a Windows machine; letting the platform default translate line endings creates spurious whole-file diffs.

## Step 5 — Report

Tell the user how many open pans were found, and highlight any with a due date coming up soon.
