---
name: pick-up
description: Run at the start of a work session to reconstruct where things were left off. Reads CURRENT.md and the latest project entries from the second brain (list_recent, scoped to this workspace), then gives a short combined brief on what was done last and where to start next. Use when the user says "pick up where we left off", starts a new session on this repo, or asks "what was I doing" / "what's next".
disable-model-invocation: true
---

# pick-up — Session Start Brief

Reconstruct context at the start of a session by combining `CURRENT.md` (hand-curated status) with the latest second-brain entries for this workspace, then give a short brief: what happened last session, and where to start now.

This is the inverse of `/recap` (which runs at session end and writes to the brain). `pick-up` runs at session start and only reads.

---

## Step 1 — Read CURRENT.md

Read `CURRENT.md` in the repo root. Focus on the **Active** and **Up Next** sections — these are the hand-curated source of truth for "what's going on" and "what's next."

If `CURRENT.md` doesn't exist, note that and rely on Step 2 alone.

---

## Step 2 — Pull the latest second-brain entries

`list_recent`'s `category` filter only accepts one value at a time, so call it **twice** — `category: project` and `category: insight` — scoped to the current workspace (the default scope already restricts to `<this workspace> + global` — don't override with `workspace: "all"`, that reintroduces the cross-project noise this skill needs to avoid). Both categories matter: `/recap` captures "Built"/"Decision"/"Open thread" thoughts as `project`, but "Learned" thoughts auto-classify as `insight` — skipping it would silently drop what was learned last session.

Start with a short window and expand only if both calls come back empty — there's no fixed default window, the goal is to reach the actual last session's entries regardless of how long ago that was:

1. Try `days: 3`
2. If empty, try `days: 7`
3. If still empty, try `days: 30`
4. If still empty, keep expanding (e.g. `90`, `365`) until you find the most recent batch of entries, or conclude there's no prior history for this workspace

Stop as soon as you get results — don't keep expanding past the point where you've found the last session's entries. Don't run `semantic_search` or `meeting_prep` — this is a lightweight, cheap status pull, not a deep retrieval.

---

## Step 3 — Synthesize a combined brief

Merge what `CURRENT.md` says with what the brain entries show into **one short narrative brief**, not two separate dumps. Cover:

- **What we did last** — the most recent work: what was built/shipped, decisions made, things learned (pull from both the brain entries and CURRENT.md's "Also this session" / "Recently Shipped" style notes)
- **Where we were planning to start** — the top of CURRENT.md's "Up Next" (respecting its stated priority order, e.g. a `plans/roadmap.md` pointer) plus any open threads surfaced in the brain entries

Keep it tight — a few sentences to a short paragraph, not a full re-listing of every item in CURRENT.md. This is a "remind me" brief, not a status report.

---

## Step 4 — Drift check (read-only)

Compare CURRENT.md's Active/Up Next sections against what the brain entries from Step 2 actually show happened.

If something in the brain (e.g. a capture describing work done, a decision, or a completed open thread) clearly isn't reflected in CURRENT.md — or contradicts it — flag it as a question. **Do not edit CURRENT.md.** Just surface it:

```
📋 CURRENT.md may be stale: <item> is listed under <section>, but the brain shows <what the entries indicate>. Want it updated?
```

**Stay silent if nothing looks stale.** Same rule as `/recap`'s drift check — this is a safety net, not a routine report. Only flag a specific, evidence-backed mismatch, never a routine "everything might be slightly out of date" note.

---

## Step 5 — Output

Give the combined brief from Step 3, followed by the drift flag from Step 4 only if one was raised. Example shape:

```
📍 Picking up second_brain

Last session: <combined narrative of what shipped/was decided/was learned>

Starting point: <top of Up Next / roadmap, plus any open thread from the brain>

[📋 CURRENT.md may be stale: ... — only if Step 4 found something]
```

---

## Rules

- **Read-only.** This skill never calls `capture_thought`, `update_thought`, or edits `CURRENT.md`. It's purely a briefing step before work begins.
- **No fixed window, but stop once found.** Expand the `list_recent` window only until you hit the last session's entries — don't over-fetch once you have them.
- **Query both `project` and `insight` categories.** `list_recent`'s category filter is single-valued, so this takes two calls — don't drop the `insight` call, it's where "Learned" captures land.
- **Stay scoped.** Never widen to `workspace: "all"` — cross-project noise (unrelated ADO tickets, other repos, Discord reminders) defeats the purpose of a quick brief.
- **No semantic_search / meeting_prep.** Those are for deliberate, on-demand deep retrieval; pick-up is a cheap routine pull of CURRENT.md + list_recent only.
- **One blended brief, not two reports.** Don't show a "CURRENT.md says X" section and a "brain says Y" section side by side — synthesize them into a single narrative.
- **Drift checks are quiet by default.** Only flag a specific, evidence-backed mismatch between CURRENT.md and the brain — and never edit the file yourself, always ask.
