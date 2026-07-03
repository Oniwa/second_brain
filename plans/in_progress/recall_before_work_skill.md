# Recall-Before-Work Skill — Stub

**Status:** stub — idea captured 2026-07-03, **needs a real planning session before implementation**. This file is a sketch to hold the idea, not a build spec.

---

## Where it came from

Originally flagged as out-of-scope in `recap_skill_improvements.md` (the OB1 "three-phase memory rhythm" — context retrieval, learning capture, instruction validation — of which `/recap` only covers the capture phase). Revisited 2026-07-03 after recalling a prior grading session (thought `11c17aed`, captured via `/recap` on a different machine 2026-07-02) that graded the brain's retrieval/synthesis B+ and flagged a residual gap: synthesis is entirely pull-based.

**Important distinction, resolved in that same discussion:** this is NOT the fix for that graded gap. The user's actual workflow already reliably pulls from the brain when planning (that's what earned the B+) — the graded gap is about blind spots they don't think to query at all, which is instead addressed by the "Proactive Resurfacing of External Insights" stub in `open_brain_improvements.md` (a digest-delivered push). This skill is a separate, lower-priority idea: automating the pull the user already does, at session start, so it happens even when they don't consciously think to invoke it.

---

## Rough shape of the idea

A `/start` or `/context` skill, run at the beginning of a work session (inverse of `/recap`, which runs at the end):

- Infer the likely topic/project from context (current directory, recent git activity, or an explicit argument)
- Run something like `get_context` / `semantic_search` / `meeting_prep` against it automatically
- Surface a short brief before work begins — open threads, recent decisions, relevant history — without the user having to remember to ask

## Evidence — cross-project noise (2026-07-03)

Simulated a fresh-session "check my second brain and CURRENT.md for status" request as a live test. `list_recent` (last 1 day, `project`+`insight` categories) returned the 7 thoughts from that session's `/recap` correctly, but mixed in with unrelated noise from other concurrent work threads: Azure DevOps/ADO flow-logging debugging (`MIS_agile_backlog_builder` source), VSP Azure Function deployment/verification threads, and Discord-submitted "watch this video by July 10" reminders — none of it second_brain-related.

This is because the brain is shared across *all* the user's projects, not scoped to whichever repo a session happens to be running in. A raw `list_recent`/`semantic_search` query has no notion of "what project am I in right now" — it returns everything recent regardless of relevance. `CURRENT.md` (hand-curated, repo-scoped) is what actually answered the status question cleanly; the brain query alone would have required manually filtering out cross-project noise to find the signal.

**Direct implication for this skill:** naive "recall relevant context at session start" is not just a wrong-guess-wastes-tokens problem (see Topic inference below) — without some notion of project/repo scope, it will *reliably* surface noise from whatever else the user has going on elsewhere (work Azure DevOps tickets, other personal projects), not just occasionally miss.

**This skill is now blocked on `plans/in_progress/project_scoping_field.md`** — a new stub plan (2026-07-03) for a dedicated project-identity field on thoughts, which is the scoping mechanism this skill needs. That plan is deliberately scoped separately (it has independent value beyond this skill and touches schema/infra across multiple capture points) — see its "Why this is its own plan" section. Don't re-litigate the scoping-mechanism design here; resolve it there first.

## Open questions for the real planning session

- ~~Project/repo scoping~~ — moved to `project_scoping_field.md`, which this skill now depends on.
- **Trigger:** manual slash command vs. some automatic hook at session start? A hook is more "recall before work" in spirit but has a much larger blast radius (runs unprompted every session).
- **Topic inference:** how does it know what to recall context *for*, without an explicit query? Wrong guess = wasted tokens and noise the user has to skim past.
- **Overlap with existing tools:** `get_context` and `meeting_prep` already exist and do on-demand retrieval well. Does this skill just wrap them with an auto-trigger, or does it need its own retrieval logic?
- **Digest/push interaction:** how does this relate to the daily digest (already a session-start-adjacent push) and the proactive-resurfacing stub above — is this redundant with those, or additive?
- **Budget/noise:** same "silence > filler" guardrail that applies to the digest push stub above should probably apply here too — an automatic recall that's wrong or irrelevant most sessions trains the user to ignore it.

## Relationship to other items

- Distinct from `open_brain_improvements.md`'s proactive-resurfacing stub (push vs. pull-at-start — see note there)
- Originates from `recap_skill_improvements.md`'s "Note on Scope" (the write-back half of the OB1 memory rhythm is handled there; this is the read-back half)
