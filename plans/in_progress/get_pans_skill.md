# `get_pans` Skill — Plan

**Status:** designed — finalized via grill-me session 2026-07-11. Ready to implement. (Working title was `get-pans`; renamed during grill-me — see Decision 7.)

---

## Summary

A new Claude Code skill, `get_pans`, that populates `open_pans.md` from the second brain's actual open "pan for gold" backlog — replacing the current manual process, where `/pan` runs an ad hoc direct PostgREST query to reconcile the tracker whenever it's noticed to be stale (last done 2026-07-01, per `open_pans.md`'s own header).

**Model: Haiku** (`claude-haiku-4-5-20251001`, matching the model ID already used elsewhere in this codebase, e.g. `process-thought`'s `HAIKU_MODEL` constant). Skill frontmatter sets the model for the *entire* skill run (same mechanism as `grill-me.md`'s `model: claude-opus-4-8`) — so Haiku isn't doing one narrow call inside a script, it's the acting model for the whole skill: running the query script, parsing due dates, and writing the file. (No intent-filtering step — see Decision 2; the structural query is the complete, correct candidate set.)

---

## Where it came from / relationship to existing plans

This overlaps substantially with **`mcp_improvements.md` §5 ("Pan Queue Visibility")**, written 2026-07-01 after the exact same problem (`open_pans.md` had drifted 9 items out of sync). That section already did the hard analysis and is prior art, not duplicated here:

- **The reliable primitive already exists and is documented there:** a `source=discord` + YouTube-URL + `status=active` query returns the exact open-pans set. `semantic_search` is blind to URLs; `list_recent` is hard-capped at 50 rows with no exact-date filter — neither is a reliable enumeration surface today.
- **Resolved relationship to §5's items** (see Decision 2): `get_pans` *depends on* §5 item #2 (`brain.py --pending-pans`) as its query backend, rather than duplicating that logic in the skill itself. §5 item #5 (the original `--sync-pans` idea) is superseded by this plan — `get_pans` is that feature, built as a skill instead of a bare CLI flag.

---

## Decisions (grill-me 2026-07-11)

### 1. Pure open-list regeneration — no historical preservation in the live file
`open_pans.md` currently holds 20 entries, **all checked off** — it's effectively already a historical log, not a live todo list. A naive DB-driven regeneration would wipe it to empty (nothing is currently open). Decided: **`get_pans` writes only currently-open items, fresh, every run.** No attempt to preserve or merge closed-out history into the live file.

**Why this is safe, not lossy:** two independent backstops make preservation unnecessary. (1) The file is git-tracked with real history (`git log -p open_pans.md`, `git show HEAD~N:open_pans.md` recover any past state). (2) More fundamentally, the underlying audit trail already exists in the second brain itself — the reminder thought's archived status plus the captured pan thoughts it produced. A markdown copy of that is redundant. At an estimated ~5 pans/week, a preserved live log would exceed 250 entries within a year for no real benefit — the DB can already answer "was this panned and what came of it" on demand.

### 2. Query mechanism — the structural filter is the complete answer; no intent classification
`get_pans` does **not** freehand-query via `semantic_search`/`list_recent` (both have documented blind spots — see §5 above) and does **not** re-implement the query logic inside the skill. Extend `scripts/brain.py` with a **`--pending-pans`** flag (this is §5 item #2, now built as the dependency) — direct REST query via the service-role key, same pattern as `brain.py`'s existing `--recent`/`--search`, returning every `source=discord` + has-URL + `status=active` thought.

**Explored and rejected during ground-truth verification (see below) — a two-stage "Haiku confirms pan-intent" design.** Initial pass at building the ground-truth baseline classified 7 of 19 structural candidates as "generic discord saves, not real pan requests" based on absence of explicit "pan"/"gold" language. Two problems surfaced when the user reviewed the actual list: (1) two of the "excluded" ones turned out to say "Pan it for gold" explicitly — missed because the query preview was truncated at 150 chars, not a real intent-classification failure; (2) more fundamentally, **the user confirmed all 19 structural candidates are legitimate pan candidates, including the ones with no pan/gold language at all** (e.g. a bare "check out this url, it contains the files referenced in my last thought"). Any URL saved via Discord and not yet resolved is worth surfacing for review, regardless of how it was phrased — the cost of one extra low-value item in the list is far lower than silently dropping something worth panning because it wasn't phrased as a request.

**Resolved: the structural filter is the complete, correct definition of "needs a pan look."** No pan-intent classification step — Haiku's role is exactly what it was originally scoped as: parse/normalize due dates from free text and format the markdown. Simpler than the two-stage design, and correctly reflects that "was this URL ever reviewed" — not "was this phrased as a request" — is the actual question `open_pans.md` needs to answer.

### 3. Cross-platform requirement — Linux + Windows
The user runs this repo on both a Linux (home) and Windows (work) machine. `brain.py` already follows portable conventions confirmed by inspection: `pathlib.Path` (not raw string path concatenation), `urllib.request` for HTTP (no shell-outs to `curl`/`wget`), no `subprocess`/`shell=True` calls anywhere. The new `--pending-pans` code must stick to the same conventions.

**One explicit requirement, not just an inherited pattern:** writing `open_pans.md` must use `newline="\n"` explicitly (Python's default text-mode write translates `\n` per-platform — LF on Linux, CRLF on Windows — which would create noisy, spurious diffs on a git-tracked file edited from both machines). Alternative/belt-and-suspenders: a `.gitattributes` rule forcing LF for `*.md`.

### 4. Due-date sort and fallback
Not every pan reminder states a due date. Decided: **sort by due date ascending when present; undated items fall back to capture-date order** (oldest first, same triage instinct as the rest of this repo, e.g. the dashboard audit page). This uses the due-date signal for items that have it without letting a missing date break the ordering for items that don't.

### 5. Read-only — never archives
`get_pans` only ever queries and writes `open_pans.md`; it never touches thought status. Archival stays exclusively `/pan`'s Phase 4 responsibility, which already does this today as a natural side effect of doing the actual panning work.

**Why, not just what:** `get_pans` runs *upstream* of panning — it populates the queue of things to pan. Determining "is this actually fully panned already" requires the same fuzzy multi-step lookup `/pan`'s own Step 0b does (direct URL search → follow companion URL → topical fallback) — real judgment work that belongs to the skill doing the panning, not the skill listing what's pending. Giving `get_pans` archive capability would duplicate that logic in two places with two possible sources of truth for "is this done."

### 6. Repo-local, not global
Matches `pan`/`synth`/`transcript`'s established precedent (per `cross_tool_skill_sync.md`'s reasoning) — `open_pans.md` lives in this repo, and pan-related work only ever happens from within `second_brain`. No global/`~/.claude/commands/` sync.

### 7. Naming — `get_pans` (snake_case), a new convention going forward
Observed during grill-me: MCP tool names follow Python/snake_case convention (`get_context`, `get_stats`, `capture_thought`) while skill names use kebab-case or bare words (`grill-me`, `pan`, `recap`, `synth`, `transcript`). Decided to standardize on snake_case **for new skills going forward, starting with this one** — `get_pans`, not `get-pans`. Explicitly **not** retroactively renaming existing skills (`grill-me` especially, already synced across this repo, `meal_planner`, and the global `~/.claude/commands/`) — that would be pure disruption (broken muscle memory, multi-repo/multi-machine churn) for a cosmetic-only win.

---

## `open_pans.md` format to match

Existing convention (see current file): a top-level header noting last-sync date and method, grouped sections, one checkbox line per pan:

```
- [ ] <original request phrasing> — <url> (saved <date>, due <date-or-phrase>) — `<thought-id>` — <status notes>
```

Per Decision 1, `get_pans` only ever writes the open/unchecked form of this — no closed-out entries.

---

## Ground-truth baseline (recorded 2026-07-11, before implementation)

Established independently of the (currently all-checked-off, possibly stale) tracker, by running the exact structural query — `source='discord' AND status='active' AND array_length(urls,1) > 0` — directly against the live DB.

**All 19 structural candidates are legitimate — the query itself is the ground truth, no further intent filtering needed** (see Decision 2 for how this was determined — an initial attempt to exclude 7 of them as "not real pan requests" was wrong on user review, including two cases where the exclusion was caused by a truncated preview missing an explicit "Pan it for gold").

| ID | Title | Captured | Note |
|---|---|---|---|
| `4c312f1e-b8c6-4ed1-8c47-28b6266ded66` | Copilot CLI skills enhancement from video | 2026-03-19 | No pan/gold language — still a valid candidate |
| `35139591-2104-4876-a57d-6bbdc1a11c8c` | AI Hero Agent Skills Reference Files | 2026-03-19 | No pan/gold language — still a valid candidate |
| `11f8a69a-ed10-4512-a9c9-f13f6dfea43a` | Claude code skills framework seven levels | 2026-03-19 | No pan/gold language — still a valid candidate |
| `888c5f47-4d06-409f-809b-c652bb7d45cb` | Read Claude Code setup guide by Boris Cherny | 2026-03-20 | No pan/gold language — still a valid candidate |
| `3d6dfbe2-550b-4618-9c6d-19d4428b4478` | Skill audit methodology for AI selection | 2026-03-25 | No pan/gold language — still a valid candidate |
| `36327525-195e-41ab-aa96-938755f90820` | AI project selection decision framework | 2026-05-17 | |
| `32d4e0c6-a0da-48ab-911f-0d28cd9106fd` | Review video on new prompting methodology | 2026-05-27 | |
| `e8561a90-4e02-413a-9d55-da50260f640e` | Review second brains video and payment deadline | 2026-06-04 | "Payment for gold" — voice-to-text mis-transcription |
| `0746c24b-3248-47ab-a897-e83276f1d794` | Review AI model selection video resource | 2026-07-03 | "paying this video for gold" — same mis-transcription pattern |
| `abaacb18-293b-4111-bb7e-1de959187120` | Review AI-human loop engineering workflow video | 2026-07-03 | "Pan it for gold" present but past the 150-char preview cutoff — caught this classification bug |
| `245adc04-f039-4d5f-8b32-a25abc4dc0b3` | Review harness engineering video by July 10 | 2026-07-03 | |
| `8987d1eb-dbb1-4fed-9255-68b5ff37b5e0` | Review AI careers video for key insights | 2026-07-03 | |
| `da5dbc97-b5a4-4183-a504-2f3b62b0b71e` | LLM CI/CD Failures Analysis and Insights | 2026-07-03 | |
| `9f7eb651-cadf-4a41-b4b7-66c0e88c408e` | Review video on imagination in AI | 2026-07-05 | |
| `4c714f61-00a1-4323-8361-fb9219eaf9d7` | Review video on writing skills for AI age | 2026-07-06 | |
| `15ee4beb-e044-4f2d-b4ad-5e628627c384` | Critical thinking video resource | 2026-07-06 | |
| `7339a478-6f84-4f86-a278-9dcf922d34b8` | Review second brains video for relevant concepts | 2026-07-06 | "Pan it for gold" present but past the 150-char preview cutoff — same classification bug |
| `9116068e-ea4b-45c7-bec0-d5c398b9f858` | Review open engine AI agent handoff video | 2026-07-08 | |
| `2f0b8480-66fa-48e8-9b97-058338d2d2a0` | Multi-agent self-checking system research | 2026-07-10 | |

**Use this list as the actual verification target** — once `get_pans` is built, its output should match these 19 exactly (allowing for legitimate drift: new pans captured since 2026-07-11, or any of these getting panned/archived in the meantime).

---

## Smoke test / verification

Before considering this implemented:

1. **`brain.py --pending-pans` matches the ground-truth baseline exactly.** Cross-check its output against the same `execute_sql` query used to build the baseline above — must return all 19 candidates (or however many exist by test time), counts and IDs matching exactly. Since the structural query *is* the answer (Decision 2), this single check covers correctness end-to-end — no separate intent-filtering test needed.
2. **`get_pans`'s markdown output includes every baseline entry**, correctly formatted, with no items dropped or invented (adjusted for legitimate drift since 2026-07-11 — new captures, or any of the 19 having been panned/archived since).
3. **Non-empty-state handling** is already covered by test 2 above, given the real current state has 19 open items (unlike the stale tracker's apparent zero) — no synthetic data needed.
4. **Due-date sort correctness.** With the real mix of dated and undated items in the ground-truth set, confirm dated-ascending-then-undated-by-capture-date ordering matches Decision 4.
5. **Line-ending check.** After a write, `git diff --stat open_pans.md` should show a clean, expected diff — no whole-file rewrite from line-ending mismatches. Confirms Decision 3's `newline="\n"` handling actually works.
6. **Windows verification** — not executable from this (Linux) session; flag for the user to confirm `--pending-pans` runs cleanly on the work PC when next convenient. Not blocking initial implementation given `brain.py`'s already-portable code patterns, but should be confirmed before relying on it from Windows.

---

## Relationship to other items

- **Depends on** `mcp_improvements.md` §5 item #2 (`--pending-pans`) as its query backend; **supersedes** §5 item #5 (the original `--sync-pans` idea — this plan is that feature, built as a skill)
- **Not related to** the `workspace` field (`plans/done/project_scoping_field.md`) — pan content is external by design (`is_external: true` always, per `pan.md`), so it's `workspace=null` and doesn't intersect with per-project scoping
