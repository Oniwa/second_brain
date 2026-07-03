# Project-Scoping Field for Thoughts — Plan Stub

**Status:** stub — captured 2026-07-03, **needs a real planning/scoping session (grill-me) before implementation.** This is a sketch to hold the idea, not a build spec.

---

## Context / motivation

Surfaced while live-testing what a fresh session would see when asking "check my second brain and CURRENT.md for status" (see `recall_before_work_skill.md`'s Evidence section). `list_recent` mixed second_brain's own captures with unrelated work from other contexts — Azure DevOps/ADO flow-logging debugging, VSP Azure Function deployment threads, personal admin — because the brain is shared across every project the user works in, with no structured way to say "this thought belongs to project X."

**There's already an inconsistent workaround in the wild:** some capture paths are free-text-stuffing a project identifier into the `source` field, which is meant for provenance (how it got captured), not project identity — e.g. `MIS_agile_backlog_builder session 2026-06-26`, `personal-context-interview`. This works by accident for exact-string grep but isn't queryable/filterable the way a real column would be, and isn't consistently applied (most second_brain captures just say `mcp`, `recap`, or `discord`, with no project marker at all).

---

## Why this is its own plan, not folded into `recall_before_work_skill.md`

This field has value independent of that skill:
- Fixes the existing inconsistent `source`-field overloading described above, regardless of whether recall-before-work ever ships
- Also relevant to `digest_backlog_filter.md`'s marker-choice question — a different field for a different purpose, but the same "add structured metadata to thoughts" design space; worth being aware of both when picking field names/conventions so the schema doesn't accumulate ad hoc parallel tagging systems
- Touches multiple capture points (Edge Function, `capture_thought` MCP tool, `recap.md`, `pan.md`, the Discord bot, whatever writes the MIS-tagged thoughts) — a cross-cutting schema/infra change, not a detail of one skill

**`recall_before_work_skill.md` is blocked on this** (its biggest open question — project/repo scoping — needs this field or something like it to exist first), but this plan should be scoped and resolved on its own terms.

---

## Rough shape of the idea

- A new **nullable** field on `thoughts` (name TBD — `project`? `project_context`? needs to read unambiguously distinct from the existing `category = 'project'` value, which means something different: category=project is "this thought is *about* a project's status/decisions"; the new field would mean "this thought was captured *while working in* project X," independent of category — an `insight`-category thought could still belong to `project = second_brain`)
- **Auto-derive where possible.** Git-backed capture contexts (recap, pan, direct MCP captures run from within a repo) can likely infer the project from the git remote/repo name automatically, with no new user burden. Non-git sources (Discord, YouTube pans, `personal-context-interview`-style captures) would need either manual tagging or no tag at all.
- **Soft scoping filter, not a hard partition.** Retrieval tools (`list_recent`, `semantic_search`, a future recall-before-work skill) should default to the current project when known, but allow an explicit override to search everything. A rigid filter would recreate the exact silo problem a unified second brain is supposed to avoid — cross-pollination (e.g. an AI-agent insight from a YouTube pan being relevant to work at a day job) is a real, intended use case, not noise to filter out by default in every context.

---

## Open questions for the planning session

- **Field name and exact semantics** — needs to be unambiguous against `category`. Also worth asking: could `topics[]` already serve this purpose via a synthetic tag convention (e.g. a `project:second_brain` topic), avoiding a schema migration entirely? Tradeoff against a dedicated typed column (queryability, avoiding topic-list pollution) needs weighing.
- **Auto-derivation mechanics** — exactly how does a git-backed capture path infer project identity (repo name? git remote URL? a config value?), and what happens for tools/sources that aren't git-backed at all (the MIS_agile_backlog_builder / personal-context-interview sources clearly aren't this same git-based Claude Code setup)?
- **Backfill strategy for ~1863 existing thoughts** — same open question already sitting in `digest_backlog_filter.md` for a different field; worth deciding once, consistently, rather than twice.
- **Default retrieval behavior** — should `list_recent`/`semantic_search` default to current-project-scoped when a project context is known, with an explicit flag to broaden, or should scoping always be opt-in? Affects every existing MCP tool's default behavior, not just new ones.
- **Where else in the schema does this interact** — `wiki_pages`/`compile_wiki.py`'s project pages already have their own project-matching mechanism (`project_definitions.json` anchor topics). Does this new field relate to or replace that, or are they solving genuinely different problems (wiki-page grouping vs. retrieval scoping)?

---

## Relationship to other items

- **Blocks** `recall_before_work_skill.md` — its biggest open question (project/repo scoping) needs this or an equivalent mechanism
- **Adjacent to** `digest_backlog_filter.md` — different field, same "new structured metadata on thoughts" design space; pick field-naming/schema conventions with both in mind
- **Possibly adjacent to** `scripts/project_definitions.json` / the wiki compiler's project-page grouping mechanism — needs clarifying whether these are the same concern or genuinely separate (see Open Questions)
