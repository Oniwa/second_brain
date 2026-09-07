---
name: pick-up
description: Run at the start of a work session, in any project, to reconstruct where things were left off. Reads CURRENT.md from the current working directory and the latest second-brain entries scoped to that directory's workspace (auto-detected, never hardcoded), then gives a short combined brief on what was done last and where to start next. Use when the user says "pick up where we left off", starts a new session on this repo, or asks "what was I doing" / "what's next".
disable-model-invocation: true
---

# pick-up — Session Start Brief

Reconstruct context at the start of a session by combining `CURRENT.md` (hand-curated status) with the latest second-brain entries for this workspace, then give a short brief: what happened last session, and where to start now.

This is the inverse of `/recap` (which runs at session end and writes to the brain). `pick-up` runs at session start and only reads.

**This skill is project-agnostic.** It must work identically in whatever repo/directory it's run from — never hardcode a specific project, repo, or workspace name anywhere in the output. Everything below derives from the current working directory at run time.

---

## Step 1 — Read CURRENT.md

Read `CURRENT.md` in the **current working directory's** root (i.e. the repo you're actually running in right now, not any repo mentioned elsewhere in this file). Focus on the **Active** and **Up Next** sections — these are the hand-curated source of truth for "what's going on" and "what's next."

If `CURRENT.md` doesn't exist, note that and rely on Step 2 alone.

---

## Step 2 — Pull the latest second-brain entries

Call `list_recent` **without an explicit `workspace` argument** — the tool auto-scopes to `<the workspace derived from your current working directory> + global` by default. Never pass `workspace: "<name>"` yourself, and never assume or hardcode which workspace that resolves to; let the tool infer it from cwd. (Only exception: never pass `workspace: "all"` either — that reintroduces the cross-project noise this skill needs to avoid.)

`list_recent`'s `category` filter only accepts one value at a time, so call it **twice** — `category: project` and `category: insight`. Both categories matter: `/recap` captures "Built"/"Decision"/"Open thread" thoughts as `project`, but "Learned" thoughts auto-classify as `insight` — skipping it would silently drop what was learned last session.

Escalate the `days` window **one step at a time, in this exact order — do not skip a step, even if you expect it to be empty**:

1. `days: 3` — check both category calls
2. If both came back empty, `days: 7` — check both again
3. If still empty, `days: 30` — check both again
4. If still empty, keep escalating one step at a time (e.g. `90`, then `365`) until you find the most recent batch of entries, or conclude there's no prior history for this workspace

Stop as soon as either call returns results — don't keep expanding past the point where you've found the last session's entries, and don't jump straight to a large window "to save a step." Don't run `semantic_search` or `meeting_prep` — this is a lightweight, cheap status pull, not a deep retrieval.

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
📍 Picking up <current directory/repo name — derived from cwd, not hardcoded>

Last session: <combined narrative of what shipped/was decided/was learned>

Starting point: <top of Up Next / roadmap, plus any open thread from the brain>

[📋 CURRENT.md may be stale: ... — only if Step 4 found something]
```

---

## Rules

- **Read-only.** This skill never calls `capture_thought`, `update_thought`, or edits `CURRENT.md`. It's purely a briefing step before work begins.
- **Project-agnostic — cwd drives everything.** Never hardcode a project/repo/workspace name in this skill's own instructions or in its output. `CURRENT.md` is read from wherever the skill is actually invoked; `list_recent`'s workspace scope is whatever the tool infers from cwd, not a name you supply.
- **No fixed window, but escalate one step at a time.** Follow the exact `3 → 7 → 30 → ...` sequence — never skip a step or jump straight to a larger window, and stop as soon as you hit results.
- **Query both `project` and `insight` categories.** `list_recent`'s category filter is single-valued, so this takes two calls — don't drop the `insight` call, it's where "Learned" captures land.
- **Stay scoped.** Never pass `workspace: "all"` — cross-project noise (unrelated ADO tickets, other repos, Discord reminders) defeats the purpose of a quick brief. Never pass an explicit `workspace` value either — always let the tool derive it from cwd.
- **No semantic_search / meeting_prep.** Those are for deliberate, on-demand deep retrieval; pick-up is a cheap routine pull of CURRENT.md + list_recent only.
- **One blended brief, not two reports.** Don't show a "CURRENT.md says X" section and a "brain says Y" section side by side — synthesize them into a single narrative.
- **Drift checks are quiet by default.** Only flag a specific, evidence-backed mismatch between CURRENT.md and the brain — and never edit the file yourself, always ask.
