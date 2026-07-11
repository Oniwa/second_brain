# `get-pans` Skill — Plan Stub

**Status:** stub — captured 2026-07-11, **needs a grill-me pass before implementation.** This is a sketch to hold the design decisions made so far, not a build spec.

---

## Summary

A new Claude Code skill, `get-pans`, that populates `open_pans.md` from the second brain's actual open "pan for gold" backlog — replacing the current manual process, where `/pan` runs an ad hoc direct PostgREST query to reconcile the tracker whenever it's noticed to be stale (last done 2026-07-01, per `open_pans.md`'s own header).

**Model: Haiku** (`claude-haiku-4-5-20251001`, matching the model ID already used elsewhere in this codebase, e.g. `process-thought`'s `HAIKU_MODEL` constant). Skill frontmatter sets the model for the *entire* skill run (same mechanism as `grill-me.md`'s `model: claude-opus-4-8`) — so Haiku isn't doing one narrow call inside a script, it's the acting model for the whole skill: querying, filtering, date-parsing, and writing the file.

---

## Where it came from / relationship to existing plans

This overlaps substantially with **`mcp_improvements.md` §5 ("Pan Queue Visibility")**, written 2026-07-01 after the exact same problem (`open_pans.md` had drifted 9 items out of sync). That section already did the hard analysis and should be treated as prior art, not duplicated:

- **The reliable primitive already exists and is documented there:** a `source=discord` + YouTube-URL + `status=active` query returns the exact open-pans set. `semantic_search` is blind to URLs; `list_recent` is hard-capped at 50 rows with no exact-date filter — neither is a reliable enumeration surface today.
- §5 proposed exactly this feature as item **#5** ("Auto-generate `open_pans.md`" via a `brain.py --sync-pans` flag) and item **#2** (`--pending-pans` / Discord `!pans`) as a lighter-weight precursor.
- `get-pans` is effectively **building item #5 as a Claude Code skill instead of a `brain.py` flag.** Worth deciding explicitly during grill-me whether this supersedes that line item in `mcp_improvements.md` or the two should coexist (e.g. skill for interactive use, script for cron).

## Design decided so far (from discussion before this plan was written)

**Why Haiku, precisely:** due dates on pan reminders are *not* a structured field — no `due_date` column exists on `thoughts`. They live as free text inside `raw_text`/`summary` (e.g. "saved 6/15, due end of June", "due end of next week"). Turning that into a sortable date requires interpreting relative natural language against the capture date — real judgment, not a mechanical lookup, and a legitimate Haiku task (same class of work Haiku already does for classification in `process-thought`). The **sort itself**, once dates are normalized, is trivial and needs no model.

**Keep the "which thoughts are open pans" determination as deterministic as possible.** The failure mode `mcp_improvements.md` §5 already diagnosed — semantic/fuzzy retrieval missing or misranking pan reminders — should not be reintroduced by having Haiku freehand-search for pans. It should call the same precise, already-identified query/filter (or a new dedicated tool, if §5 item #1's first-class `pan_status` gets built first) rather than relying on `semantic_search`.

## `open_pans.md` format to match

Existing convention (see current file): a top-level header noting last-sync date and method, grouped sections (e.g. "Explicit 'pan for gold' items", "Recent discord submissions"), and one checkbox line per pan:

```
- [ ] <original request phrasing> — <url> (saved <date>, due <date-or-phrase>) — `<thought-id>` — <status notes>
```

Closed-out entries carry rich annotation (which thoughts it was panned into, when, reminder-archival status) — this history has real value and should not be silently discarded on regeneration (see Open Questions).

---

## Open questions for the grill-me session

- **Overwrite vs. merge with existing file.** `open_pans.md` currently holds a valuable audit trail — closed-out items annotated with exactly which thoughts they were panned into and when. Does `get-pans` regenerate the whole file from the DB each run (simple, but risks losing that annotation history unless it's also captured somewhere structured), or does it need to merge new open items in while preserving already-checked-off history verbatim?
- **Query mechanism.** Reuse the existing tools (`list_recent` with a wide window, filtered client-side) the way `/pan`'s manual reconciliation does today, or does this finally justify building `mcp_improvements.md` §5 item #1 (a first-class `pan_status` field / dedicated `find_by_url`-style tool) as a prerequisite? Affects reliability a lot — worth resolving before the skill leans on a specific query shape.
- **Due-date parsing reliability and fallback.** Not every pan reminder states a due date. What's the sort position for undated items (last? by capture date instead?), and how much should the skill trust Haiku's interpretation of ambiguous phrasing like "due end of next week" without a stated reference date?
- **Scope of write access — read-only list generation, or does it also archive?** `/pan`'s own Phase 4 already archives the reminder thought once a source is fully panned. Should `get-pans` stay strictly read/list-generating (populate the file, leave archival to `/pan` as today), or also handle marking items done when it detects they're already fully panned (like the historical entries in the current file show `/pan` doing manually)?
- **Repo-local, not global.** Given `open_pans.md` lives in this repo and pan/synth/transcript are already established as repo-local-only skills (per `cross_tool_skill_sync.md`'s reasoning — only ever invoked from within `second_brain`), `get-pans` should be repo-local too. Flagging as a fast-resolve item, not a real open question, so grill-me doesn't need to spend time on it.
- **Naming.** `get-pans` reads slightly differently from this repo's other skill names (`pan`, `recap`, `synth`, `grill-me` — verb or verb-phrase, not `get_`-prefixed like the MCP tool naming convention `get_context`/`get_stats`). Minor, but worth a beat during grill-me in case a different name reads more consistently alongside the existing skill set.

## Relationship to other items

- **Builds on** `mcp_improvements.md` §5 (Pan Queue Visibility) — treat that section's analysis as prior art; don't duplicate the reliable-primitive research here
- **Not related to** the `workspace` field (`plans/done/project_scoping_field.md`) — pan content is external by design (`is_external: true` always, per `pan.md`), so it's `workspace=null` and doesn't intersect with per-project scoping
