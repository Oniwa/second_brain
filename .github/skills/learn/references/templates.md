# Artifact templates

Reference for `/learn` Steps 1, 2, and 5. All files live under `<LEARNING_LAB_PATH>/<topic-slug>/`.

## `MISSION.md` — two-pass write

**Draft (end of Step 1):** `Slug`, `Started`, `Mode`, `Target competency level`, `Mission statement`. Leave `Bounded exercise`, `Competency contract`, and `Predeclared criteria` as `(pending — finalized at Step 2)`.

**Finalized (end of Step 2):** fill in the three pending sections. Do not start the exercise or teach-back before this pass is done.

```markdown
# Mission: <topic title>

- **Slug:** <topic-slug>
- **Started:** <date>
- **Mode:** 2 (professionally-actionable / capability-building)
- **Target competency level:** <awareness | practitioner | independent practitioner | architect>
- **Bounded exercise:** <one sentence — what will be built/run/measured>

## Competency contract
By the end of this mission I can:
1. <"I can ..." statement>
(5 statements at practitioner; 6 at independent practitioner / architect)

## Predeclared criteria
- **Teach-back rubric:** <core mechanism / mission-specific relevance / tradeoff-or-boundary>
- **Failure-analysis rubric:** <highest-risk failure mode / misleading-success failure mode, each with detection>
- **Exercise success measure:** <observable output; for decision exercises, the metric(s) committed before the run>

## Mission statement
<the falsifiable, narrowed statement from Step 1 — not an open-ended study>
```

## `SOURCES.md` — end of Step 2

```markdown
# Sources: <topic title>

## From second brain (prior captures — treated as saved belief, not fact)
- <thought id / title> — <one line on relevance>

## Freshly researched for this mission
- **Official/primary:** <source + link> — <what it establishes>
- **Practitioner:** <source + link> — <what it establishes>

## Disagreements or gaps found
<state plainly, or "None">
```

If second-brain tools were unreachable, say so here ("degraded grounding: live research only").

## `RECORD.md` — end of Step 5

```markdown
# Record: <topic title>

- **Slug:** <topic-slug>
- **Mission:** <one line, copied from MISSION.md>
- **Outcome:** <paused | completed | graduated>
- **Gate results:** teach_back=<passed|unmet|not_attempted>, exercise=<passed|unmet|not_attempted>, failure_analysis=<passed|unmet|not_attempted>

## Cold-attempt baseline
<the user's unaided pre-teaching guess, verbatim or close paraphrase>

## Demonstrated understanding
<what the teach-back showed, in the user's own words>

## Exercise + verification evidence
<what was built/run/measured; the observable output; the actual result, not "done">

## Teach-back result
<rubric copied verbatim from MISSION.md Predeclared criteria, with grading applied>

## Failure modes + tests
<rubric copied verbatim from MISSION.md, with the failure modes explored and how each would be detected>

## Remaining gaps
<unmet criteria after retry, outstanding diagnose-or-transfer check, missing prerequisites, absorbed prerequisites>

## Recommended next step
<free text, with a one-line reason>

## Artifact paths
- Mission: `<topic-slug>/MISSION.md`
- Sources: `<topic-slug>/SOURCES.md`
- Exercise: `<topic-slug>/exercises/...`
```

For an "I just need the answer" exit, write: outcome `paused`, all gates `not_attempted`, reason "user requested direct answer, not a verified cycle".

## `learning_lab/README.md` index row

One row appended or updated per topic; Status uses the same vocabulary as `RECORD.md`'s Outcome.

```markdown
| Topic slug | Title | Status | Last updated |
|---|---|---|---|
| rag-reranking-evaluation | RAG reranking evaluation | graduated | 2026-10-02 |
```

## Per-topic layout

```
<topic-slug>/
├── MISSION.md
├── SOURCES.md
├── lessons/
├── exercises/
└── RECORD.md
```

(`REVIEW.md` is Mode 3 only — not created in v0.1.)
