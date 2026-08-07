# Wiki Incremental Compile — Synthesize From Delta + Existing Page

Opened 2026-08-07, as the leading candidate for the topics/projects cost-control follow-up — **ahead of `wiki_cowork_synthesis.md`, which is now the fallback if this doesn't work out.** Design not finalized — stub with a strong, evidence-backed leaning, needs its own grill-me pass and a small quality pilot before broad implementation.

---

## The idea

Today, `compile_wiki.py` re-synthesizes a page from its **entire raw thought corpus** every time `--skip-unchanged` sees any `thought_count` delta, however small. Instead: fetch only the thoughts captured **since the last compile**, fetch the **existing compiled page**, and ask the model to update/merge the new material into the existing page rather than regenerating from scratch.

## Why this looks like the right first move

Quantified against real data (2026-08-07, calibrated from the actual `topic-ai-agents.md` file and the session's real Sonnet 5 pricing):

| | Full resynthesis (today) | Incremental (proposed) |
|---|---|---|
| Input | Full raw corpus: 331 thoughts × ~387 tok/thought ≈ **128K tokens** | Existing page (~7,400 tokens, measured from the real 29,769-char `topic-ai-agents.md`) + only new thoughts since last sync (~hundreds to ~2K tokens for a typical week's delta) ≈ **~9-10K tokens** |
| Output | Full page (~7,400 tokens) | Full page (~7,400 tokens) — unchanged, same either way |
| Est. cost, "AI agents" | ~$0.28/compile event | ~$0.03-0.05/compile event |
| Reduction | — | **~85-90% per event** |

Applied to the ~$20/month modeled steady-state estimate (`wiki_weekly_cron.md`, `CURRENT.md` 2026-08-07): plausibly drops to **~$3-5/month**. Bigger win than the Cowork route, and doesn't require standing up a new platform or auth mechanism — just a different prompt and a delta query. Input dominates cost today because it scales with total corpus size; incremental compile decouples cost from corpus size entirely (cost scales with the *existing page* + the *delta*, both roughly constant/small regardless of how much history has accumulated).

## The real risk: quality drift

This is the same "incremental compile" option flagged earlier in the design conversation, not a new idea free of downsides. Once a page is only ever updated from its own prior output + new deltas, it never re-derives from the raw source material it already synthesized. Known failure modes:
- **Compounding drift** — a framing choice, omission, or subtle error from one pass persists and compounds over months of incremental patches, since nothing ever resets against ground truth.
- **Structural rigidity** — new content tends to get stapled onto the existing section structure rather than the page naturally reorganizing as a topic's shape evolves (e.g. a new subtheme large enough to deserve its own section might just get appended to whatever section already existed).

## Mitigation: periodic full re-baseline

Mirrors the cadence pattern already shipped for content-creator people (`wiki_compile_cost_control.md`) — cheap incremental updates most cycles, but a **periodic full resynthesis from the complete raw corpus** (candidate: quarterly, same as the people cadence, though the right interval here is unverified) to correct accumulated drift and let the page restructure. Two-tier cadence: incremental on delta (cheap, frequent, keeps freshness), full recompile on a timer (keeps quality anchored to source data).

## Open questions for the eventual grill-me pass

- **Prompt design.** `TOPIC_SYSTEM_PROMPT`/`PERSON_SYSTEM_PROMPT` assume "synthesize a page from a pile of raw thoughts." A merge/update prompt is a different task ("here's an existing page and new facts — integrate cleanly, restructure where it no longer fits") and needs its own design and testing, not just a smaller version of the existing prompt.
- **"Since last sync" tracking.** Compare thought `created_at` against the page's `last_compiled_at`? Needs a reliable per-page watermark — verify this doesn't fight `--skip-unchanged`'s existing `thought_count`-equality bookkeeping.
- **Re-baseline cadence.** Quarterly (mirroring people), a fixed N-incremental-cycles count, or something drift-aware? Unverified — the people cadence number itself was a judgment call, not a measured optimum.
- **Scope: topics only, or people/projects too?** People already have a cadence fix (skip entirely rather than update) — could incremental compile replace that with "cheap incremental every week" instead of "skip for 90 days"? Worth comparing once this is proven out.
- **Quality validation.** Needs a real pilot — implement the merge prompt for 1-2 topics, compare output quality against a full resynthesis on the same data, before rolling out broadly. Drift risk is a known category, not a measured one yet for this specific prompt/corpus.
- **Interaction with `--skip-unchanged`.** Likely replaces the any-delta full-skip logic for topics entirely (since incremental runs are now cheap enough to just always run on any delta) — full recompile becomes its own separate cadence-gated path, not the default.

## Relationship to `wiki_cowork_synthesis.md`

**Try this first.** No new platform, no auth setup, no Windows-parity or context-limit unknowns — just a prompt and a query change, on infrastructure that's already built and verified working. If the quality-drift risk turns out to be unmanageable in practice (the pilot shows real degradation that periodic re-baselining doesn't fix), fall back to the Cowork route, which sidesteps the drift question entirely by keeping full-resynthesis quality but changing who pays for it.

## Recommended next step

A small, cheap pilot: implement the incremental merge prompt for 1-2 real topics (candidates: something mid-size and well-characterized), run it against real deltas, and read the output side-by-side with what a full resynthesis produces on the same data. Validate before designing the full rollout (delta-tracking mechanism, re-baseline cadence, `--skip-unchanged` integration).

## Related

- `plans/in_progress/wiki_compile_cost_control.md` — the topics/projects any-delta cost problem this is solving; that file's "Follow-up opened 2026-08-07" section is the diagnosis
- `plans/in_progress/wiki_cowork_synthesis.md` — fallback if this doesn't pan out
- `plans/in_progress/wiki_weekly_cron.md` — the cron this eventually unblocks (Step 5, currently held)
- `plans/roadmap.md` #7
