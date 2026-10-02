---
name: learn
description: Run a focused, verified learning cycle on a professionally relevant technical topic, producing a working exercise and a concise learning record. Use when the user wants to learn, study, or get up to speed on an AI, agentic-systems, or technical topic they intend to apply.
disable-model-invocation: true
compatibility: Uses second-brain MCP tools (get_context, semantic_search, capture_thought) and live web research when available; degrades to web research alone. Requires a local clone of the learning_lab repo via LEARNING_LAB_PATH. Targets GitHub Copilot CLI only.
---

# learn — Verified Learning Cycle (v0.1, Mode 2 only)

Answers one question: *how do I acquire enough verified understanding of a professionally relevant topic to apply it correctly?* One ~60-minute sitting, five steps. Source design: `plans/learning_system/learning_system.md`.

Reference files (read the one named at each step, not all up front):
- `references/rubrics.md` — competency levels, rubric construction rules, exercise contract, gates, outcomes, remediation
- `references/templates.md` — `MISSION.md`, `SOURCES.md`, `RECORD.md`, README index row
- `references/storage-and-resume.md` — preflight, commit, resume, graduation capture

Not built yet, do not simulate: routing between modes, Mode 1 quick explanations, Mode 3 mastery tracks, spaced repetition, evidence-classification schema.

---

## Preflight

Follow `references/storage-and-resume.md` § Preflight: read `LEARNING_LAB_PATH`, confirm it is a git repo, and confirm the tree is clean. Stop on any failure. Write nothing until all three pass.

If the user named an existing topic slug, follow § Resume instead of starting Step 1.

---

## Step 1 — Mission + depth

Ask exactly one question: *"What are you trying to learn, and what decision or thing you're building does it support?"*

- Need `topic` and `application`. If the user gave only a bare topic, ask once more for the missing `application`. Do not proceed without it.
- **Curiosity-only** (no planned application): decline with *"This sounds like Mode 1 (quick explanation), which isn't built yet; want to give it a bounded application instead, or just ask me directly?"* Do not run the cycle.
- `target_competency`: infer from the application if implied; otherwise default to **practitioner** without asking. Never ask the user to pick from the level list.
- State the normalized mission in one sentence and continue to Step 2 without waiting, unless the user objects.
- Derive a kebab-case `topic-slug`. Write the **draft** `MISSION.md` (see `references/templates.md`).

**Cold-attempt check:** before teaching, ask once: *"Before I explain: what's your current guess at how this works, or how you'd approach it?"* One short answer, ungraded. If the user has none, move on. Keep it verbatim for `RECORD.md`.

---

## Step 2 — Grounded explanation

Do these in this exact order. Read `references/rubrics.md` before item 2.

1. **Source.** Call `get_context` with the mission (fall back to `semantic_search` if nothing relevant). Then run live research: at least one primary/official source and one real practitioner source (an implementer or maintainer, not an influencer roundup); add an evaluation/failure-analysis source if needed. Cite second-brain notes as *saved beliefs* and ask for confirmation before relying on them. If sources disagree or nothing authoritative exists, say so plainly, downgrade the expected outcome to "needs experiment", and continue. If second-brain tools are unreachable, proceed on research alone and note it in `SOURCES.md`.
2. **Predeclare.** Write the teach-back rubric, failure-analysis rubric, exercise success measure, and the derived competency contract. Write the bounded exercise. Finalize `MISSION.md` and write `SOURCES.md`. Nothing downstream starts before this is saved. If a missing foundational concept would block interpreting the result, apply the prerequisite override.
3. **Teach**, in exactly three short parts, one explanation each: (a) **Simple model** — one analogy or plain explanation at the single depth that fits, never several ages; (b) **Why it matters here** — one paragraph tied to this mission; (c) **Concrete mapping** — one paragraph onto the user's actual system (ask a clarifying question first if missing). Add a short grounding note: what came from the second brain vs. live research. Give other depths only if the user asks.
4. **Hand off.** State the exercise contract (type, timebox, baseline, success measure, observable output) before starting.

---

## Step 3 — Applied exercise

Run the exercise per its contract inside the timebox, under `<topic-slug>/exercises/`. Scaffold, explain syntax, and help debug the user's own attempt. Never produce the exercise's conclusion for them. Apply the blocked-exercise fallback from `references/rubrics.md` if a prerequisite is missing; if nothing is runnable, stop and go to Step 5 with outcome `paused`.

---

## Step 4 — Teach-back + completion gate

Grade three independent checks against the rubrics written in Step 2, copied verbatim from `MISSION.md`: teach-back, exercise verified, failure analysis. Get the user's answer **in their own words before any commentary**. Never expand or shrink criteria after the fact.

On a miss: name the unmet criterion, re-teach only that part, retry once; on a second miss, log a Remaining Gap and move on. Never supply the teach-back's answer, even if asked twice; offer the plain explanation and end the cycle.

For independent practitioner / architect targets seeking `graduated`, run the diagnose-or-transfer check (see `references/rubrics.md`), or mark the competency provisional and cap at `completed`.

---

## Step 5 — Record + next step

1. Write `RECORD.md` and update the `learning_lab/README.md` index row (templates in `references/templates.md`). Outcome is exactly one of `paused` / `completed` / `graduated`; gates are `passed` / `unmet` / `not_attempted`. Never imply durability.
2. Commit locally per `references/storage-and-resume.md` § Step 5 commit. No push.
3. If outcome is `graduated` and the commit succeeded, call `capture_thought` per § Graduation capture.
4. Tell the user the outcome, gate results, the commit, and a recommended next step with a one-line reason.

---

## "I just need the answer" exit (any step)

Stop teaching and give the plain answer. Skip teach-back and grading. Write a `RECORD.md` with outcome `paused`, all gates `not_attempted`, reason "user requested direct answer, not a verified cycle". Commit per Step 5. This is a legitimate exit, not a failure.

---

## Rules

- Never fabricate a passed gate.
- Never write inside `second_brain`; artifacts go only to `LEARNING_LAB_PATH`.
- Never push, clone, or create the learning_lab repo.
- Never ask the user to choose a competency level or an age depth cold.
- Predeclared criteria are fixed once written.
