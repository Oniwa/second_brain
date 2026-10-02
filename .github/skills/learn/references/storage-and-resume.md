# Storage protocol, resume, and graduation capture

Reference for `/learn` Preflight, Step 5, and resume.

## Location

Artifacts live in a separate git repo, `learning_lab`, not in `second_brain`. v0.1 targets GitHub Copilot CLI only and requires a **pre-cloned local copy** found via the `LEARNING_LAB_PATH` environment variable (expected value: `C:\projects\learning_lab`).

## Preflight (before Step 1 writes anything)

1. Read `LEARNING_LAB_PATH`. If unset: stop, ask the user to set it (or give a path for this session). Never guess a default and never fall back to writing inside `second_brain`.
2. If the path doesn't exist or isn't a git repo: stop and ask the user to clone it. Never `git clone` or create it.
3. **Dirty-tree check:** run `git status --porcelain` in that repo. If there are uncommitted changes, stop and tell the user. Do this now, before any file is written, not just before the Step 5 commit.

The skill does not clone, discover multiple candidates, pull, or push in v0.1.

## Step 5 commit

After writing `RECORD.md` and updating the `README.md` index row:

1. Stage the **entire `<topic-slug>/` directory** plus `README.md` — one commit per session, since earlier artifacts were never committed on their own.
2. Commit with message `<topic-slug>: <outcome>` (e.g. `rag-reranking-evaluation: completed`), including the Co-authored-by trailer.
3. **Local commit only. No push.** Tell the user the commit happened and that syncing is manual.

If the commit fails, tell the user and skip any graduation capture.

## Resume (exact slug only)

No fuzzy matching, no "what was I working on" inference. The user names the topic slug; if the request is ambiguous (e.g. "continue my RAG work" with several RAG slugs), ask for the exact slug. Read `MISSION.md` and `RECORD.md` (if present) for that slug.

Re-enter at the step **after** the last one that produced a durable artifact:

| State found | Resume at |
|---|---|
| `MISSION.md` drafted only | Step 2 |
| `MISSION.md` finalized + `SOURCES.md`, no exercise output | Step 3 |
| Exercise output exists, grading not done | Step 4 |

- Gates already `passed` in a partial `RECORD.md` carry over; only `unmet` / `not_attempted` gates are retried.
- Exception: an "I just need the answer" pause (all gates `not_attempted`) restarts the teaching cycle fresh at Step 2.
- A topic already `graduated` is never re-edited. Start a new, explicitly named follow-on mission with its own slug.

## Graduation capture

Only when outcome is `graduated`, and **only after** the local commit succeeds, call `capture_thought`:

```
Graduated: <topic> — <one-line mission>. Demonstrated: <competency level reached>. Outcome: <what the competency contract confirmed>. Full record: learning_lab/<topic-slug>/RECORD.md
```

Don't force a category. A second graduation (new slug) gets its own capture; never edit a prior one. If second-brain tools are unavailable, tell the user and skip.
