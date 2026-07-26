# Person identity resolution — canonical names across the brain

_Stub filed 2026-07-26. Trigger: `jbarksdale` and `john-barksdale` are the same person (the brain's owner). Investigation showed the owner is not a special case — **person identity is unresolved system-wide**, so this plan is the general mechanism, with the owner as its first consumer._

## The finding

**117 distinct `people` values across 1556 mentions**, producing 56 person pages. Three distinct failure modes, all measured 2026-07-26:

### A. Bare first name colliding with full names — 8 clusters

| bare | full-name candidates |
|---|---|
| `Caleb` (8) | `Caleb Browning` (4) |
| `Cody` (4) | `Cody Nedved` (2) |
| `Drew` (3) | `Drew Ford` (1) |
| `Katelyn` (11) | `Katelyn Conley` (4) |
| `Mark` (1) | `Mark Pecaut` (3) |
| **`David` (1)** | `David Ondrej` (20), `David Purser` (3), `David Anthony Hall` (1) — **ambiguous** |
| **`John` (10)** | `John Barksdale` (6), `John Ousterhout` (1) — **ambiguous** |
| **`Simon` (7)** | `Simon Scrapes` (49), `Simon Willison` (2) — **ambiguous** |

Five are near-certain merges; three have multiple candidates and **must not be auto-merged on string match**.

### B. Case / punctuation variants — 3 clusters

| variants |
|---|
| `Nate B. Jones` (639) · `Nate B Jones` (266) · `NateBJones` (1) |
| `Dan Shapiro` (4) · `danshapiro` (1) |
| `Simon Willison` (2) · `simonwillison` (1) |

`people_aliases.json` already maps `Nate B Jones` → `Nate B. Jones`, so the *page* is correct — but **266 mentions still carry the wrong string in the data**, so every people-based query misses them. This is the clearest evidence that compile-layer aliasing is not sufficient.

### C. Machine identifiers captured as people — 4 values

`jbarksdale` (11) · `danshapiro` (1) · `simonwillison` (1) · `rduictrsvc@leggett.com` (1)

Note `danshapiro` and `simonwillison` are exactly the prefixes in `EXTERNAL_SOURCE_PATTERN` — the classifier is lifting the *source prefix* into the `people` array. `rduictrsvc@leggett.com` is a service-account email, not a person at all.

## Why the current mechanism is insufficient

`people_aliases.json` + `build_reverse_map()` fixes **wiki compilation only**. The underlying `thoughts.people` arrays keep every variant, so `semantic_search`, `get_context`, `meeting_prep`, and the dashboard all stay fragmented. Today the file holds 3 hand-written entries against a problem with ~15 clusters — it does not scale and nothing surfaces new drift.

## Scope

### 1. Detection — make duplicates visible
A reusable report (script flag or `--dry-run` section) that surfaces candidate clusters using the three rules above:
- normalized-equality (strip case, punctuation, spaces) → high confidence
- bare-token prefix of a longer name → needs adjudication, list all candidates
- no-space lowercase / email-shaped values → likely machine identifiers

Must be **re-runnable**, not a one-time audit — new people arrive continuously.

### 2. Canonicalization — one identity, at the data layer
Decide the durable representation, then apply it:
- **Option A:** keep `people_aliases.json` as the source of truth, but apply it to `thoughts.people` via a backfill migration (pattern: `010_workspace_backfill.sql`) so queries and pages agree.
- **Option B:** a `people` table with canonical names + variants, replacing the JSON file. Heavier, but supports merge history and per-person metadata.

Whichever wins, ambiguous clusters (David / John / Simon) need **human adjudication** — the tool proposes, the user disposes.

### 3. Prevention — stop the drift at capture
- `process-thought` should normalize `people` on write against the canonical map, so variants never enter.
- Fix the source-prefix leak putting `danshapiro` / `simonwillison` into `people`.
- Reject or strip email-shaped and service-account values.

### 4. The owner — a distinct design question
`jbarksdale` (11) + `John Barksdale` (6) + part of `John` (10) are all the brain's owner. Beyond the merge, decide whether the owner should have a person page **at all**: every thought in the brain is already theirs, so a self page is a different kind of object than a page about an external figure. Options: merge into one page / exclude the owner entirely / a distinct "me" page type prompted for open commitments and recurring patterns rather than third-party biography.

## Known blockers / interactions

- **Orphan deletion does not exist.** `compile_wiki.py` has no delete path; `stale` is only ever written `False`. Every merge *creates* dead pages nothing cleans up — same gap hit by the workspace-only project work (`plans/done/project_page_implementation.md` → Risks). ~15 merges means ~15 orphans; this plan probably needs `--prune` to exist first, or it trades one mess for another.
- **Recompile cost.** Merging changes `thought_count` on affected person pages, so they recompile. Bounded (56 person pages, most untouched).
- **`Nate B. Jones` is 905 mentions across variants** — by far the largest entity in the brain. Any migration touching `people` must be verified against it specifically.

## Open questions

- Data-layer canonicalization (Option A) or a real `people` table (Option B)?
- Adjudicate the 3 ambiguous clusters manually now, or build the detection report first and adjudicate in bulk later?
- Should the owner have a person page at all?
- Is there a real colleague named John, or is every bare `John` the owner?
