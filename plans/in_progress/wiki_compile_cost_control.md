# Wiki compile cost control — page exclusion and recompile cadence

_Stub filed 2026-07-26, from cost analysis of the workspace-only project scoping compile run (44 pages, ~$3, 29m 9s)._

## The finding

A single page dominates compile cost. Measured on the 2026-07-26 run:

| | |
|---|---|
| Pages compiled | 44 |
| Thoughts fed to Sonnet | 1727 |
| **`person-nate-b-jones` alone** | **905 thoughts — 52% of the run's entire input volume** |
| Est. cost of that one page | ~$1.30–1.50 of the ~$3 |
| Avg chars/thought | ~1400 (≈350K input tokens for the Nate page in one call) |

Per-page cost was $0.068 vs $0.046 on the 418-page full run — expected, because `--skip-unchanged` correctly skipped the cheap pages and recompiled the expensive ones.

**Why this matters for the cron (roadmap #1):** Nate B. Jones is the dominant capture source, so his thought count changes nearly every week. `--skip-unchanged` compares `thought_count`, so *any* delta triggers a full recompile of all 905 thoughts — **~$1.40/week in perpetuity for one page**, growing as it grows. The other 55 person pages combined cost less.

## Content creators vs colleagues — a real, detectable category

Measured across all `people` values with ≥2 mentions, using `is_external` OR a source matching `EXTERNAL_SOURCE_PATTERN`:

| Category | People | Thought-mentions | external % |
|---|---|---|---|
| Content creators (Nate B. Jones, Matt Pocock, Simon Scrapes, Karpathy, Dylan Davis, Matt Wolfe, …) | **33** | 1382 | 90–100% |
| Actual colleagues (Katelyn, Ben Brown, Drew, Mark Pecaut, …) | **23** | 102 | 0% |

The split is **almost perfectly binary** — the `ext%` column is either ≥90% or 0%, with essentially nothing between. So the external ratio classifies "source I read" vs "person I work with" without a hand-maintained list. Person pages are overwhelmingly (93% of mentions) about content creators.

## The key question — resolved 2026-07-26: the page is mostly duplication

**Asked:** is a single Nate page that updates constantly worth it, given his content is already synthesized across topic pages — which is where retrieval actually happens?

**Measured, and the answer is largely no:**

| | |
|---|---|
| Nate-mentioned thoughts | 906 — **44% of the entire brain** |
| Already reaching >=1 compiled topic page | **874 (96%)** |
| Reaching no topic page at all | **32** |
| Distinct topic pages he feeds | **300 of 366** (82% of the topic wiki) |

Deleting the page orphans **32 thoughts, not 905**. An earlier draft of this plan called it "plausibly the most valuable page in the wiki" — that was asserted without checking coverage and is **wrong**.

**The residual 15%.** The compiled page splits three ways:
- *Key Interactions & History* — a chronology of panning sessions, not knowledge. Duplication.
- *140+ footnote source list* — duplication.
- *Recurring themes/frameworks* — **not derivable from topic pages**: comprehension-over-generation, dark code, agent species framework, the Karpathy Loop, judge layer, One-Minute Test. Topic pages are organized by subject, so "AI agents" mentions the judge layer; nothing conveys that these are **one person's coherent worldview**. Cross-topic attribution to a thinker is the one thing a source page does that a topic page structurally cannot.

**Conclusion: cadence, not deletion — but quarterly, not weekly.** The unique 15% is also the slowest-changing content on the page, so weekly regeneration buys nothing. Quarterly saves ~92% of the recurring cost and keeps the through-line; exclusion saves 100% and loses it. Quarterly dominates unless the framework list isn't wanted — in which case exclusion is clean and defensible.

**This generalizes to all 33 content creators**: their pages duplicate topic pages by construction, because their content *is* topic material. Colleague pages are plausibly different in kind (meetings and interactions are person-shaped, not topic-shaped) — **unverified; check before applying any blanket rule to person pages.**

## Options

1. **`exclude` flag in the people config** — what the long tail needs. Mechanically identical to the project display-name override map shipped 2026-07-26: give `people_aliases.json` the same `string | object` normalization so `{"Matt Wolfe": {"exclude": true}}` works with no schema migration.
2. **Change threshold instead of any-delta** — only recompile when `thought_count` moves by more than N (or N%). Cheap, and directly targets the weekly Nate churn. Probably the highest value-per-effort item here.
3. **Per-page thought cap** — compile the N most recent thoughts for very large entities instead of full history. Largest saving; loses long-tail fidelity on exactly the page where history may matter most.
4. **Prompt caching** — real but small. The system prompt is static across pages of a type, but it's dwarfed by the per-page thought payload; expect single-digit percent.

## Interactions

- **Roadmap #5 (person identity resolution)** — same file, same load path. #6 must already decide the canonical-name representation for `people_aliases.json`; the `exclude` flag should be settled in the same pass rather than migrating the file twice. Note Nate is also the worst dedup case: `Nate B. Jones` (639) + `Nate B Jones` (266) + `NateBJones` (1) = 906 — the alias file already merges them at compile time, which is *why* the page is 905 thoughts and why it is expensive.
- **Roadmap #6 (AI token / cost tracker)** — this analysis had to be reconstructed from character counts because no per-call cost data exists. This is the motivating example for Phase 1 instrumentation.
- **Roadmap #1 (weekly cron)** — the ~$1.40/week recurring charge only starts once the cron is live. Worth deciding before Step 5 activates it, not after.

## Open questions

- Exclude the thin content-creator long tail, or keep all person pages and control cost purely via cadence/caps?
- Should content-creator pages be a distinct entity type with their own prompt ("what I've learned from this source") rather than the third-party-biography framing person pages use today?
- Threshold shape for option 2: absolute delta, percentage, or "N weeks since last compile, whichever first"?
