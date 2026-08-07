# Pan Skill Improvements

Improvements surfaced from a heavy `/pan` session on 2026-07-02 — five pans run
back-to-back (mjTgkm-h__M, b4d32pBa3UY, HgAQOkG_v8c, A4zMyjkL0Dc, Zp8lr6IzUnQ),
four of them consecutive Nate B. Jones videos. This file consolidates pan-skill
improvements that were previously scattered across `mcp_improvements.md`,
`wiki_implementation.md`, and `personal_digest_fix.md` (done), plus net-new items
found this session.

**File to modify:** `.claude/commands/pan.md` (skill-side changes only — no schema/code).

**Status:** ✅ implemented 2026-07-12 via `/grill-me` review. A1 dissolved (see its
entry below), A2 dropped from this file's scope (real fix landed upstream, see below),
A3 stays rejected, B1 and B2 shipped into `pan.md` with refinements from the review.
`wiki_implementation.md`'s overlap spec was updated to match.

**Live verification not yet run.** The plan's own checklist (run a 2+ pan batch,
confirm merges/trims get narrated and near-dups surface below the old 65% floor) is
still outstanding — deliberately not blocking this plan's done-status on it (decision
2026-07-12: verify opportunistically on a future real pan; if that surfaces a problem,
it gets its own new plan rather than reopening this one).

---

## Design principle — two human curation gates

The user curates at two points, both upstream of and within the skill:
1. **Gate 1 (feed → pan list).** The user watches a video and decides it is worth
   panning *before* it becomes a "to pan" thought. The pan queue is already
   human-vetted.
2. **Gate 2 (pan → brain).** During the pan dry-run, the user picks which insights
   actually get captured.

**Implication for the skill:** `/pan` runs entirely downstream of the user's judgment.
It must **never gatekeep whether a source is worth panning** (that was decided at Gate
1) or suppress captures because a creator is well-represented. Its job is narrow:
extract thoroughly, avoid capturing the same *concept* twice, and make Gate 2 easy with
good trims/merges. This is the root reason A3 (creator-saturation nudge) is rejected.

---

## Cross-reference — already covered elsewhere (do NOT duplicate here)

These pan pain points already have owning plans. Listed so this file is a complete
index; implement them in their home plan.

| Pain point | Owning plan | Status |
|---|---|---|
| Dedup via `semantic_search` on a URL is unreliable (embedding-only, blind to URLs) | `mcp_improvements.md §4 find_by_url` | Planned, Phase 4, high priority. Fix: `/pan` Step 0b calls `find_by_url` first as authoritative dedup. |
| Pan reminders pile up invisibly; `open_pans.md` drifts out of sync | `mcp_improvements.md §5 Pan Queue Visibility` | Planned, Phase 4. `--sync-pans` auto-generates the tracker; `--pending-pans`/`!pans` enumerate; first-class `pan_status`. |
| Phase 4 reminder archival needs the full UUID (manual re-query) | `mcp_improvements.md §5` | Systemically resolved once pan-queue primitives exist. Minor skill-note only if desired. |
| `is_external: true` always; `{platform}: Author - Title` source format; dual-source (YouTube+Substack) handling | `personal_digest_fix.md` (done) | Shipped. |
| Phase 2.5 per-draft wording trim | `wiki_implementation.md` line 341 | Shipped (this is per-draft trim, NOT the merge/proactive-cut behavior in §A below). |

---

## A. Net-new items (no existing plan)

### A1. Intra-session / intra-batch overlap check  ⭐ highest priority

**Problem.** Phase 2 overlap-checks each item against the *settled* brain, but when
several related sources are panned in one sitting, a new capture can duplicate one
made **minutes earlier in the same session**. The current skill has no notion of
same-session captures as a distinct watch category.

**Evidence (2026-07-02).** Panning A4zMyjkL0Dc right after HgAQOkG_v8c, the "loop
anatomy" item (trigger/sources/memory/safe-actions/boundary/record) overlapped the
five-part-loop thought `60f19e8e` (memory/method/boundary/receipt/judgment) captured
in the *previous* pan — ~58% similar. It was caught only because the agent remembered
capturing it; it was **invisible to the skill's own overlap check** because 58% falls
below the 65% "say nothing" floor (see A-refine B2).

**Why it matters.**
- Near-dup thoughts split retrieval relevance — one concept returns two half-answers.
- Content-fingerprint dedup (done plan) is **exact-text only**; it explicitly lists
  near-duplicate detection as out of scope, so it will not catch this.
- Risk is highest exactly during batch-panning — the core backlog workflow, where
  topics cluster by creator/theme.
- Relying on the agent's working memory of what it captured 10 minutes ago is fragile.

**Proposed change (pan.md).** In Phase 2, add:
> When panning multiple sources in one session, overlap-check each candidate against
> thoughts captured **earlier in this same session/batch**, not just the pre-existing
> brain. Treat same-session captures as a first-class watch category and surface them
> even below the normal soft-warning floor (see threshold note). Maintain a short
> running list of this session's captured titles/concepts to compare against.

**Pros:** clean retrieval; trustworthy batch pans; no reliance on memory.
**Cons:** a few more overlap searches per pan (tokens); minor instruction complexity.
**If left as-is:** simpler skill, but one lapse in attention ships a silent duplicate
you won't notice until a search returns twins.

**Resolution (2026-07-12): dissolved, no separate `pan.md` instruction needed.**
`capture_thought` embeds and stores immediately, so by the time a *second* `/pan`
invocation runs Phase 2's `semantic_search`, anything captured in a prior invocation is
already in the searchable brain — same-session awareness was never actually missing.
The A1 evidence (58% similarity, invisible) was purely a **threshold** problem, fully
fixed by B2's recalibration below. The other half of what A1 gestured at — items that
duplicate each other *within* one pan's own extraction list, before either is captured
— isn't a search problem at all (nothing's in the DB yet); it's what B1's merge pass
below now handles. A1 is kept here only as the evidence record for why B1 and B2 exist.

---

### A2. Transcript cleanup step

**Problem.** Step 0a fetches and reads the `.txt` transcript but the skill never says
to delete it. The file is left uncommitted in the repo root.

**Evidence (2026-07-02).** All five pans left a transcript in the repo root; each was
deleted manually. (Unrelated to the recap plan's "no transcript dumping," which is
about not capturing transcript *content* into the brain.)

**Proposed change (pan.md).** Add to Phase 4 (or a note in Step 0a): after captures
are complete, delete the fetched transcript `.txt` from the working directory.

**Pros:** no orphaned artifacts / accidental commits.  **Cons:** none material.

**Resolution (2026-07-12): dropped from `pan.md` scope — fixed at the root instead.**
Investigation during the `/grill-me` review found the litter was never a `second_brain`
problem: `second_brain`'s repo root was already clean, and Step 0a deliberately doesn't
know the transcript's absolute path ("the transcript skill handles all machine-specific
path resolution"), so `pan.md` has no principled way to `rm` a file whose location it
never learns. The actual bug was in `youtube_transcript/main.py`: its default output
path was resolved relative to the *caller's* CWD instead of the tool's own directory,
so the litter's location depended entirely on where `/pan` happened to be invoked from
(landing in `second_brain` on the established Windows workflow, but in
`youtube_transcript`'s own root when invoked differently on Linux). Fixed by anchoring
the default output path to `Path(__file__).resolve().parent / "transcripts"` in that
project — deterministic regardless of caller CWD, on either platform. Shipped, tested
(95/95 passing after updating the tests that had asserted the old CWD-relative
behavior), committed, and pushed to `youtube_transcript`'s `origin/development`
(commit `0fc0af2`). Accumulation inside that project's own `transcripts/` folder is
accepted as fine — manual cleanup there, if ever needed, is out of scope for `pan.md`.

---

### A3. Density-fatigue guidance  — REJECTED (misaligned with user workflow)

**Original idea.** When a creator is already heavily represented, raise the capture
bar and prefer fewer captures, on the theory that aggregate overlap is rising.

**Why it's rejected (user input, 2026-07-02).** The user deliberately watches *every*
Nate B. Jones video and hand-picks which to add — they consistently find his takes
valuable. A dense Nate footprint is therefore the **intended result of deliberate
source-level curation, not accidental bloat.** A "creator is well-represented → raise
the bar" heuristic is actively backwards here: it would penalize the exact creator the
user has chosen to over-index on, and risk dropping a genuinely novel take.

**The correct guard is concept-level, not creator-level.** The real failure mode is
*the same concept captured twice*, regardless of who said it — which is already handled
by A1 (intra-batch overlap) and B2 (threshold recalibration). Source volume is not a
signal to suppress; per-concept duplication is.

**Decision:** do **not** add any creator/source-saturation nudge to `pan.md`. Rely on
A1 + B2 for concept-level de-duplication and leave source-level curation to the user,
who already does it upstream by watching everything and choosing what to pan.

---

## B. Refinements to existing behavior

### B1. Make trims AND merges first-class in Phase 2.5

**Problem.** The shipped Phase 2.5 covers per-draft *wording* trim, and item-level
capture/skip. It does **not** cover two behaviors the user requested on every pan:
1. The agent **proactively recommending which whole items to cut** (with reasons),
   rather than waiting to be asked.
2. **Merging/folding multiple extracted items into one draft** — the inverse of the
   "one thought per concept" rule, for when several extracted items are really one
   concept.

**Evidence (2026-07-02).** The user asked "what are your recommended trims?" on all
five pans. Folding/merging happened constantly: GLM Draft 5 folded 3 items; merged
"context lock-in" drafts 3+4; folded the agent-demo test into agents-as-loop-managers;
folded loop-anatomy into the taxonomy draft.

**Proposed change (pan.md).** In Phase 2.5, add:
> Proactively present a short "recommended trims & merges" list before asking to
> capture: name items to cut (with a one-line reason each), and identify any
> extracted items that are really one concept and should be **folded into a single
> draft**. "One thought per concept" cuts both ways — split genuinely distinct ideas,
> but consolidate items that only look distinct.

**Pros:** matches actual usage; leaner, higher-signal captures; less user prompting.
**Cons:** slightly longer dry-run output.

**Resolution (2026-07-12): shipped, split into two sub-steps rather than one bundled
instruction.** The `/grill-me` review surfaced that merges and trims naturally happen
at opposite ends of Phase 2.5: a **merge** is an item-level decision that must happen
*before* drafting (drafting first and merging after wastes a draft), while a **trim**
is a wording-level edit that requires the draft text to already exist. `pan.md`'s
Phase 2.5 is now three steps — Step 1 Merge check (before drafting, narrated inline,
e.g. "merging items 6 and 9 into one draft"), Step 2 Draft (unchanged), Step 3
Recommended trims (proactive, after drafting, e.g. "Draft 3: cut the closing sentence
— it's inference the reader can already draw"). Neither step gets its own stop-and-wait
gate — both ride the existing single "Capture these now, or any changes first?"
question, per user preference, **but both must explicitly state what they changed and
why** so that single gate remains a real review point rather than a rubber stamp.

---

### B2. Recalibrate overlap thresholds

**Problem.** The shipped bands (hard ≥85%, soft 65–84%, silent <65%) sit too high for
same-author/same-topic clusters. `wiki_implementation.md`'s overlap spec is even
coarser (single 85% threshold) and does not address calibration.

**Evidence (2026-07-02).** Genuinely adjacent/near-duplicate concepts consistently
landed at **55–64%**: five-part-loop vs loop-anatomy 58%; briefing vs hidden-loop
57–59%; several harness near-dups 62–70%. Almost nothing crossed 65% even when it was
a real duplicate worth skipping. The 65% silent floor hid exactly the matches that
mattered (and is what made A1 invisible).

**Proposed change (pan.md).** Lower the soft-warning floor to ~55%, or add:
> For same-author or same-topic clusters, manually review matches in the 55–64% band —
> embedding similarity understates conceptual overlap there. Do not treat <65% as
> automatically clear.

**Pros:** surfaces the real near-dups; unblocks A1.  **Cons:** more soft-warnings to
adjudicate (some will be false positives); mild dry-run noise. **Note:** this points
the *opposite* direction from the existing 85% spec in `wiki_implementation.md` — that
spec should be reconciled to this one.

**Resolution (2026-07-12): hard-lowered, not the softer "manually review" alternative.**
Chose the mechanical floor (55%, always shown) over the judgment-based alternative
("manually review the 55–64% band for same-author clusters") — the softer version
relies on the agent *recognizing* a same-author/same-topic cluster before applying
extra scrutiny, which is exactly the recognition failure that caused the original miss.
A mechanical floor removes that judgment call entirely; the cost is occasional
false-positive soft warnings on genuinely unrelated 55–64% matches, cheap to dismiss
during Phase 2.5. Shipped in `pan.md`'s Phase 2 (bands now: hard ≥85% / soft 55–84% /
silent <55%) and reconciled into `wiki_implementation.md`'s overlap spec the same day.

---

## Priority summary

| # | Item | Priority | Status (2026-07-12) |
|---|---|---|---|
| B1 | Trims + merges, split into merge-pass (pre-draft) + trim-pass (post-draft) | **High** | **Shipped** in `pan.md` Phase 2.5. |
| B2 | Recalibrate thresholds to hard ≥85% / soft 55–84% / silent <55% | **High** | **Shipped** in `pan.md` Phase 2 and reconciled into `wiki_implementation.md`. |
| A1 | Intra-batch overlap check | — | **Dissolved** — fully covered by B2 (cross-pan case) + B1 (within-pan case). No separate `pan.md` change. |
| A2 | Transcript cleanup | — | **Resolved upstream** — root cause fixed in `youtube_transcript/main.py` (commit `0fc0af2`, pushed). Not a `pan.md` concern. |
| A3 | Density-fatigue nudge | **Rejected** | Unchanged — misaligned with user workflow. Dense creator footprint is deliberate curation, not bloat. Guard concepts (B1/B2), not creators. |

---

## Verification
1. Read the updated `pan.md` and confirm B1 (merge pass + trim pass, both narrated,
   both riding the single Phase 2.5 gate) and B2 (55%/85% bands) are present as
   written above; confirm no creator/source-saturation nudge was added (A3 stays
   rejected) and no transcript-deletion step was added (A2 resolved elsewhere).
2. Run a batch of 2+ related pans next session — confirm the agent surfaces a
   same-session near-dup below the old 65% floor (proves B2), and proactively states
   merges and trims with explicit reasons before asking to capture, without being
   asked (proves B1).

## Note on scope
Skill-file changes only. The tooling-side fixes (`find_by_url`, pan-queue visibility,
`--sync-pans`) remain owned by `mcp_improvements.md §4–5`; once those land, revisit
Step 0b to make `find_by_url` the primary dedup and drop the fuzzy 3-part lookup.
