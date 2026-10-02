# Rubrics, gates, and outcomes

Reference for `/learn` Steps 2, 4, and 5. Source of truth: `plans/learning_system/learning_system.md`.

## Competency levels

- **awareness** — can explain the concept and recognize when it applies. Cannot build or troubleshoot.
- **practitioner** — can implement a bounded solution *with guidance*. Default target when nothing else is implied.
- **independent practitioner** — can implement and troubleshoot without step-by-step help; knows common failure modes going in.
- **architect** — can select between competing designs and defend tradeoffs for a specific situation.

A mission's target may exceed what one session reaches. Say so in the record rather than overstating.

## Construction rules (write all of these in Step 2, before teaching)

**Teach-back rubric** must cover: (1) the core mechanism, (2) why *this* mission needs it, (3) at least one tradeoff or boundary condition (when it is *not* the right call). It does not cover failure modes or success measurement.

**Failure-analysis rubric** must cover: (1) the single highest-risk failure mode for *this* mission, (2) one failure mode that produces a **misleading success signal** (looks fine, isn't) — each with how it would be detected/tested. Risk-based, not count-based: pick the two that matter, not the first two that come to mind.

**Exercise success measure**: the observable output that settles the mission's question. For decision exercises, name the metric(s) that decide the yes/no **before the run**; never choose or adjust them afterward.

**Competency contract** (derived mechanically, not invented):
1. core mechanism [teach-back rubric]
2. doing the bounded exercise [exercise contract]
3. a tradeoff/boundary condition [teach-back rubric]
4. a failure mode [failure-analysis rubric]
5. a concrete yes/no or recommendation answering the mission's own question
6. (only for independent practitioner / architect) the diagnose-or-transfer capability

Practitioner = 5 items; independent practitioner or architect = 6.

Grade only against what was written. Never expand or shrink criteria after the fact.

## Applied-exercise contract (Step 2 → 3 handoff)

State all of these before starting Step 3:

- **Type** — coding (something is built/run) or decision (a comparison produces a recommendation), chosen by whether the mission's `application` is a build or a decision.
- **Timebox** — default 30–45 minutes of a ~60-minute session.
- **Baseline/control** — what "without the concept" looks like, for comparisons.
- **Success measure** — committed before the run.
- **Observable output** — the concrete artifact or result that will exist when done.

**Blocked-exercise fallback:** if a prerequisite is missing, downgrade to the smallest exercise still runnable and note it in `RECORD.md`. If nothing is runnable, stop, do not grade, set `exercise=not_attempted`, outcome `paused`, and name the missing prerequisite in Remaining Gaps. Do not stall fixing the environment.

You may scaffold starter code, explain syntax, and help debug the user's own attempt. You may never produce the exercise's *conclusion* or the teach-back's *answer* for them.

## The five decisions

Three independent checks, each graded separately:

- **Teach-back passed** — the user's own words satisfy the teach-back rubric.
- **Exercise verified** — the exercise produced the observable output defined in its contract (it ran and produced a result, not merely "code written").
- **Failure-analysis satisfied** — the failure-analysis rubric is met, independently of teach-back.

Two roll-ups:

- **Completed** — all three checks passed. Means *guided, session-bounded understanding*, not durable mastery.
- **Graduated** — every competency-contract item is checked off. At independent practitioner / architect targets, additionally requires the **diagnose-or-transfer check**: the user fixes a seeded fault or adapts an unfamiliar variant (not rehearsed during teaching) with materially less scaffolding than Step 3 gave. If no such variant fits the timebox, mark the competency **provisional**, name the follow-up check, and cap the session at `completed`.

## Outcome vocabulary

- **Session outcome** (exactly one; used in `RECORD.md`, `README.md` Status, and the commit message): `paused` / `completed` / `graduated`.
- **Gate results** (three separate `RECORD.md` fields): `teach_back`, `exercise`, `failure_analysis`, each `passed` | `unmet` | `not_attempted`.
  - "I just need the answer" exit → all three `not_attempted`.
  - No runnable exercise → `exercise=not_attempted` only; `teach_back` keeps whatever it reached.
  - Any gate `not_attempted` forces outcome `paused`.
- **Recommended next step** — free text in `RECORD.md`, not a controlled vocabulary.

## Remediation (Step 4)

On a miss: name the specific unmet criterion, re-teach only that part, retry once. On a second miss, log it under Remaining Gaps and end the session. A miss on one check does not block the others from passing. Never supply the teach-back's answer in the user's place, even if asked twice — offer the plain explanation and end the cycle.

## Retention

`completed` and `graduated` both mean "verified today, under guidance." Never imply durability or that retention is being tracked.

## Prerequisite override

If a missing foundational concept actually blocks correct interpretation of the mission's own result, name it, teach the minimum needed, and record it in `RECORD.md` as an absorbed prerequisite. Don't work around it silently.
