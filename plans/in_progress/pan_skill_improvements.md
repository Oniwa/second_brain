# Pan Skill Improvements

Improvements surfaced from a heavy `/pan` session on 2026-07-02 — five pans run
back-to-back (mjTgkm-h__M, b4d32pBa3UY, HgAQOkG_v8c, A4zMyjkL0Dc, Zp8lr6IzUnQ),
four of them consecutive Nate B. Jones videos. This file consolidates pan-skill
improvements that were previously scattered across `mcp_improvements.md`,
`wiki_implementation.md`, and `personal_digest_fix.md` (done), plus net-new items
found this session.

**File to modify:** `.claude/commands/pan.md` (skill-side changes only — no schema/code).

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

---

### A3. Density-fatigue guidance  (lowest priority — a nudge, not a mechanism)

**Problem.** When a creator is already heavily represented, marginal novelty drops and
aggregate overlap rises, but nothing in the skill raises the capture bar.

**Evidence (2026-07-02).** Four consecutive Nate B. Jones pans; by the 3rd–4th the
agent manually reminded itself to "be ruthless." The harness concept hit 62–70%
against existing captures; the moat/lock-in cluster was densely pre-represented.

**Why it has independent value.** Pairwise overlap checks (A1 / B2) are *per-thought*
and miss **aggregate saturation** — 10 items each individually <60% similar can
collectively be the 5th rehash of one author's worldview. Only source-level awareness
catches that.

**Honest caveats.**
- Soft heuristic — "well-represented" is hard to make precise.
- Risks the *opposite* failure: under-capturing a genuinely novel angle out of fatigue.
- Largely a backstop the **user already provides** via the dry-run + trim step.

**Proposed change (pan.md).** One line in Phase 2:
> If this source's creator/topic is already densely represented in the brain, raise
> the capture bar and prefer fewer, higher-novelty captures — but never skip a
> genuinely new angle just because the creator is familiar.

**Recommendation:** ship as a one-line nudge only; accept it may be redundant once B2
lands. Do not build a mechanism for it.

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

---

## Priority summary

| # | Item | Priority | Rationale |
|---|---|---|---|
| A1 | Intra-batch overlap check | **High** | Real data-quality bug that occurred this session; near-dups silently split retrieval. |
| B1 | Trims + merges first-class | **High** | Requested on every pan; the biggest gap between skill-as-written and skill-as-used. |
| B2 | Recalibrate thresholds (65%→~55%) | **Medium** | Unblocks A1; surfaces the real overlap band. Reconcile with wiki spec. |
| A2 | Transcript cleanup | **Medium** | Trivial, removes repo-root litter. |
| A3 | Density-fatigue nudge | **Low** | One-line nudge; largely subsumed by A1/B1/B2 and the user's own trim step. |

---

## Verification
1. Read the updated `pan.md` and confirm A1, A2, B1, B2 (and optionally A3) are present.
2. Run a batch of 2+ related pans next session — confirm the agent surfaces a
   same-session near-dup below 65% (A1/B2) and proposes trims/merges unprompted (B1).
3. Confirm the transcript `.txt` is deleted after each pan (A2).

## Note on scope
Skill-file changes only. The tooling-side fixes (`find_by_url`, pan-queue visibility,
`--sync-pans`) remain owned by `mcp_improvements.md §4–5`; once those land, revisit
Step 0b to make `find_by_url` the primary dedup and drop the fuzzy 3-part lookup.
