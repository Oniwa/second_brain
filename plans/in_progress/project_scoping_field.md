# Project-Scoping Field for Thoughts (`workspace`) — Plan

**Status:** designed — finalized via grill-me session 2026-07-08. Ready to implement. Supersedes the original 2026-07-03 stub (kept below under "Original motivation").

---

## Summary

Add a nullable `workspace text` column to `thoughts` that records **which project/repo the capture happened in** (provenance/context), so retrieval tools can default to the current project instead of returning cross-project noise. `null` = unscoped/global (external knowledge + anything unknown), and is **always eligible** in every scope so cross-pollination is preserved.

Motivating failure: a fresh-session `list_recent` in `second_brain` returned its own captures mixed with unrelated day-job noise (ABU deploys, MIS agile_backlog_builder, AI governance) because the brain is shared across every project with no capture-context marker.

---

## Decisions (grill-me 2026-07-08)

### 1. Mechanism — dedicated typed column
`workspace text` on `thoughts`, following the `is_external` migration pattern (`ALTER TABLE ADD COLUMN` + one-shot backfill). **Not** a synthetic `topics[]` tag (pollutes wiki/stats/keyword surfaces) and **not** overloading `source` (that's provenance of *how* it was captured — the existing inconsistent hack this plan replaces).

### 2. Name & semantics — `workspace`
- Single text slug, **nullable**.
- Means "captured *while working in* project X." **Orthogonal to `category='project'`** (which means "this thought is *about* a project"). An `insight`-category thought can still have `workspace='second_brain'`.
- The word "workspace" (not "project") is deliberate — avoids permanent confusion with `category='project'`.
- **Slug value = the git-toplevel directory basename** so historical backfill and go-forward derivation always agree.

### 3. Derivation (client-side)
Order of resolution at capture time:

```
external?  → null
else       → .workspace override file at git-toplevel (if present)
           → git rev-parse --show-toplevel  → basename
           → cwd basename
           → null
```

- **External gate (hardened):** treat as external (→ `null`) if `is_external = true` **OR** `source` matches `^(youtube|substack|article|github|synthesis|danshapiro|simonwillison):`. Belt-and-suspenders because `is_external` is unreliable (see Known Bug). External insight must stay global/cross-pollinating — never stamped to whatever repo the `/pan` ran from.
- **`.workspace` override file:** a small git-tracked file at a repo root containing the canonical slug. Handles **one logical project spanning multiple repos** without a central registry. Required for **ABUCW**, which is currently several repos feeding one project (consolidation planned); each ABU repo gets `.workspace` = `abucw`, and the future consolidated repo carries the same file.
- **Edge Function is server-side** (no git/fs) — it just accepts and stores a `workspace` payload param, exactly like `source`/`is_external`. All derivation happens in the client (the MCP server's `captureThought`, which `recap` and `pan` both call).
- **Discord bot** is server-side → sends no `workspace` → `null` (honest; the bot can't know).

### 4. Retrieval — scoped-by-default (current + null)
Tools default to `workspace = <current> OR workspace IS NULL`, where `<current>` is derived from the server's cwd using the same rule. Rationale: the noise problem was the entire trigger; opt-in scoping leaves the default broken and fails the auto-run `recall_before_work` consumer. Including nulls preserves cross-pollination (pans still surface).

- **Override:** `workspace: "all"` (or CLI `--all-workspaces`) disables the filter for a deliberate cross-project sweep.
- **Transparency:** every tool response prints a one-line `scope: <workspace> (+global)` (or `scope: all`) header so it's always clear whether the view is scoped or full.
- **Affected tools:** `semantic_search`, `list_recent`, `get_context`, `meeting_prep` (MCP) and `brain.py` `--search`/`--recent` (CLI).

### 5. Relationship to `project_definitions.json` — separate
Different problems: `workspace` = capture-context scoping for *retrieval*; `project_definitions.json` = subject/topic-anchor grouping for *wiki project-page compilation*. Kept fully independent for this plan.
- **Future, out of scope:** `compile_wiki.py` *could later* union `workspace = X` as a supplementary first-party signal for project-page grouping (a thought captured in-repo is strong evidence it belongs to that project page even with thin topic tags). Noted so the two tagging systems aren't conflated later. Not built now.

### 6. Backfill — targeted, exact predicates, is_external-gated
The column defaults to `null` on `ALTER TABLE`, so pans (external) and genuinely-unknown captures need **no action** (null = global = correct). Only the day-job "work noise" is tagged — the exact cross-project rows that motivated this plan and that won't fade from relevance-ordered search via volume.

**Backfill mapping (43 rows; verified against live DB 2026-07-08):**

| `workspace` slug | Rows | Real working dir / basis |
|---|---|---|
| `agile_backlog_builder` | 19 | `C:\projects\ai\agile_backlog_builder` |
| `abucw` | 18 | multi-repo → `.workspace` override; single slug for all ABU rows |
| `idea_center_ai_policy` | 6 | `C:\projects\ai\idea_center_ai_policy` (AI governance work) |
| *(null — excluded)* | 13 | external Substack pan ("Seven questions…"), `is_external=true` |

**Critical backfill rule:** use **exact per-slug `source` predicates gated on `is_external = false`** — NOT a broad keyword regex. During grilling a broad regex false-matched all 13 rows of an external Substack pan (its "governance/agent" wording), which must stay `null`. The `is_external=false` gate + precise source strings prevents re-siloing external insight.

Backfill slugs deliberately equal the go-forward git-toplevel basename so history and future captures land in the same workspace.

`personal-context-interview` (10 rows) and all other untagged captures stay `null` (cross-cutting personal/unknown context — not a project to scope out).

---

## Implementation surface (7 touch points)

1. **`supabase/migrations/007_workspace.sql`** — `ALTER TABLE thoughts ADD COLUMN workspace text;`, add index (`gin`/btree per query needs), + the three exact-predicate backfill `UPDATE`s (gated `is_external=false`).
2. **Edge Function `process-thought`** — accept `workspace` in the request body; store on insert and in update mode (passthrough, like `source`/`is_external`).
3. **MCP `captureThought`** — derive workspace client-side (external-gate → `.workspace` file → git-toplevel basename → cwd basename → null); include in the Edge Function payload. Single change covers direct captures **+ `recap` + `pan`** (both call `capture_thought`).
4. **MCP query tools** (`semantic_search`, `list_recent`, `get_context`, `meeting_prep`) — derive current workspace from cwd; default filter `workspace = current OR IS NULL`; support `workspace:"all"`; add `workspace` to selects; print the `scope:` header.
5. **`semantic_search` SQL RPC** (`001_init.sql`) — add `filter_workspace text default null`; `WHERE (filter_workspace IS NULL OR t.workspace = filter_workspace OR t.workspace IS NULL)`. New migration.
6. **`scripts/brain.py`** — same scoping for `--search` / `--recent` (lower priority; can follow the MCP change).
7. **Discord bot** — no change (sends no `workspace` → null, correct).

Plus (one-time, per work repo): add a `.workspace` file to each ABU repo containing `abucw`.

---

## Known bug captured for separate cleanup (do NOT block this plan)

**`is_external` mislabeling.** 213 rows have clearly external `source` (`youtube:`/`substack:`/`article:`/`github:`) but `is_external = false` (~15% of external content). The migration-006 backfill (`raw_text ILIKE '%Source:%'`) missed them, and some capture path drops the flag.

- **Data cleanup:** `UPDATE thoughts SET is_external = true WHERE source ~* '^(youtube|substack|article|github|synthesis|danshapiro|simonwillison):' AND is_external = false;`
- **Root-cause fix:** find and fix the capture path that omits `is_external` on external captures.
- Independent of this plan — the hardened external gate (Decision 3) already tolerates the flag being wrong, so `workspace` does not depend on this being fixed first.

---

## Verification

- `007` applied: `workspace` column exists, nullable, indexed.
- Backfill counts match exactly: `agile_backlog_builder`=19, `abucw`=18, `idea_center_ai_policy`=6; the 13 Substack rows remain `null`.
- A capture from inside `second_brain` lands `workspace='second_brain'`; a `/pan` from the same repo lands `workspace=null` (external gate).
- A capture from an ABU repo carrying `.workspace=abucw` lands `workspace='abucw'`.
- `semantic_search`/`list_recent` from `second_brain` return second_brain + null rows only, with a `scope: second_brain (+global)` header; `workspace:"all"` returns everything with `scope: all`.
- No external/pan row is ever stamped with a non-null workspace.

---

## Relationship to other items

- **Unblocks** `recall_before_work_skill.md` — this is the scoping mechanism its biggest open question depended on.
- **Adjacent to** `digest_backlog_filter.md` — different field, same "structured metadata on thoughts" design space; backfill approach (exact predicates, leave-unknown-null) is a reusable precedent for its shared backfill question.
- **Separate from** `scripts/project_definitions.json` / wiki project-page grouping (Decision 5), with a noted future-only enhancement.

---

## Original motivation (2026-07-03 stub, preserved)

Surfaced while live-testing what a fresh session would see when asking "check my second brain and CURRENT.md for status" (see `recall_before_work_skill.md`'s Evidence section). `list_recent` mixed second_brain's own captures with unrelated work — Azure DevOps/ADO flow-logging debugging, VSP/ABU Azure Function deployment threads, AI governance, personal admin — because the brain is shared across every project the user works in, with no structured way to say "this thought belongs to project X." Some capture paths were already free-text-stuffing a project identifier into `source` (`MIS_agile_backlog_builder session 2026-06-26`, `personal-context-interview`), which is meant for provenance, not project identity, and isn't queryable/consistent. This plan replaces that hack with a real typed column.
