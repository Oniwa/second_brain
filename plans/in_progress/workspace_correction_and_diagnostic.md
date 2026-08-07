# Workspace correction + unscoped-capture diagnostic

_Stub filed 2026-07-26, split out of the workspace-only project scoping grill (`plans/done/project_page_implementation.md` follow-up). Deliberately deferred: the scoping change ships first, this closes the gap it opens._

## Why this exists

Project pages are moving to **workspace-only scoping** (a project *is* a workspace; topic-anchor matching is retired). That fixes the old "project thoughts don't appear on their page" bug, but installs a narrower version of it:

**A thought captured outside its project's repo lands with `workspace = NULL` and silently never appears on that project's page.** Sources: Discord capture from a phone, a `/pan` run, capture from `~` or a sibling repo.

Two things are missing to make that safe, and they're only useful together:

1. **No way to see it.** Nothing reports project-category thoughts that have no workspace.
2. **No way to fix it.** `update_thought` (`mcp/src/server.ts:288`) exposes `title`, `summary`, `category`, `people`, `topics` — **not `workspace`**. A mis-scoped thought currently cannot be corrected through any interface. (Note: the tool's description at server.ts:766 claims it updates "any other field" — inaccurate, fix while here.)

A diagnostic without the correction path is just recurring noise, which is why these ship as one unit.

**Assessed low urgency:** most capture happens via the `recap` skill from inside the project repo, which derives the workspace correctly. This is a correctness backstop, not a live pain point.

## Scope

### 1. Add `workspace` to `update_thought`
- Add to the args interface and the MCP tool input schema (`server.ts` ~288 and ~766).
- Must accept explicit `null` to *clear* a workspace (re-globalize a wrongly-stamped thought), not just set one — distinguishing "omitted" from "set to null" in the JSON schema is the fiddly part.
- Fix the misleading "any other field" description text.
- Consider whether the audit dashboard should expose it too (overlaps the inline-edit work in the dashboard plans).

### 2. Repurpose `get_unmatched_project_thoughts()`
`scripts/compile_wiki.py:589` currently reports `category=project` thoughts matching no project *anchor topic*. Anchor topics are going away, so it must be rewritten to report:

> `category = project` AND `workspace IS NULL` AND not external

The external exclusion reuses `EXTERNAL_SOURCE_PATTERN` / `is_external` — external content is *designed* to stay global (`deriveCaptureWorkspace`, server.ts:101), so it must never be flagged as a scoping mistake.

### 3. Surface it where it will actually be seen
A report that only prints during a manual `--dry-run` is invisible once the weekly cron runs unattended. It should reach the cron's existing Discord completion DM as a one-liner — e.g. `⚠️ 4 project thoughts captured with no workspace`, ideally with IDs so they can be fixed via `update_thought`.

**Sequencing constraint:** that DM is the same delivery path as the digest-truncation bug (roadmap #2 — `digest_chunking_fix.md`). Adding lines to a message that already truncates makes it worse. **Ship the chunking fix first.**

## Open questions

- Should the diagnostic also cover `category != project` thoughts with a NULL workspace, or is project-category the right narrow scope?
- Auto-suggest a workspace (e.g. infer from topics/content) or just report and let the user decide?
- Does a bulk-correction path matter, or is one-at-a-time `update_thought` enough at this volume?

## Depends on

- Workspace-only project scoping shipping first (it defines the failure mode).
- `digest_chunking_fix.md` shipping first (shared Discord delivery path).
