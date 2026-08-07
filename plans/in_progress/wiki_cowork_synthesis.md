# Wiki Synthesis via Claude Cowork Scheduled Tasks

Opened 2026-08-07, during the wiki cron's first live activation. **Design not finalized — this is a stub with a strong leaning, not a spec. Needs its own grill-me pass and a small proof-of-concept before implementing.**

> ⏸️ **Demoted to fallback, same day.** `plans/in_progress/wiki_incremental_compile.md` is now the leading candidate — quantified savings comparable or better (~85-90% per-event token reduction, modeled ~$3-5/month vs. this route's "free but unverified fit"), no new platform/auth/Windows-parity unknowns, builds on infrastructure already shipped and verified working. **Try incremental compile first.** Return to this route only if incremental compile's quality-drift risk turns out unmanageable in practice.

---

## Problem this solves

`plans/in_progress/wiki_compile_cost_control.md`'s "Follow-up opened 2026-08-07" section found that the any-delta-triggers-full-recompile behavior fixed for content-creator *people* pages (via quarterly cadence) is general — topic pages have the same problem, and unlike person pages, **topics have no duplication-based escape hatch.** Measured directly: for the biggest topics, 90%+ of their thoughts also reach *other* topic pages, but that's normal multi-tagging, not redundancy — there's no more-canonical layer above topics the way topics are more canonical than person pages. So a cadence/threshold fix for topics means accepting real staleness on pages that are large specifically *because* they're where the user's most active, most original thinking lives — the opposite of "safe to deprioritize."

Every mechanism discussed that stays inside the current Python/API pipeline forces a choice between cheap, automatic, and fresh — pick two:

| Option | Cheap | Automatic | Fresh |
|---|---|---|---|
| Delta/size threshold (accept staleness) | ✅ | ✅ | ❌ — stale on exactly the pages that matter most |
| Manual Claude Pro-session skill (user triggers) | ✅ | ❌ — depends on remembering | ✅ (when run) |
| Incremental compile (send only new thoughts, merge) | Partial — still metered API, cheaper per-call not free | ✅ | ✅, but new drift-risk failure mode |
| Headless Claude Code under Pro/Max auth | ✅ (if supported) | ✅ (if supported) | ✅ | — genuinely unverified whether this auth path supports batch/headless use |

## The leaning: Claude Cowork Scheduled Tasks

Confirmed via research 2026-08-07 (not internal knowledge — verified against current Anthropic docs):
- **Billing:** scheduled Cowork tasks run on the user's **subscription plan** (Pro/Max/Team), not metered API billing — separate from the credit system.
- **Scheduling:** genuine recurring automation (daily/weekly/monthly), cloud-hosted — doesn't require the user's machine to be online.
- **Platform:** full feature parity on **Windows** (an earlier search pass found "macOS only, Windows expected mid-2026" — that was stale; a Windows launch has already shipped).
- **Connectors:** Supabase is an official Cowork connector, with the same access a manual Cowork session would have — querying `thoughts`/`wiki_pages` and writing results back is in scope.

This is the only option that hits cheap + automatic + fresh **with confirmed product support**, rather than an unverified assumption. It doesn't ask the user to trade freshness for cost on the pages where that trade is most costly.

## What's NOT yet verified (why this isn't ready to build)

1. **Context/output limits at scale.** Confirmed only that Supabase querying works in principle — not confirmed that a single scheduled task can handle a large synthesis pass (e.g. `AI agents` at 331 thoughts, ~350K input tokens as an API call) within whatever context/output constraints Cowork's execution environment has. Untested.
2. **Bookkeeping integration.** `compile_wiki.py`'s `--skip-unchanged` logic depends on `wiki_pages.thought_count` / `last_compiled_at` staying in sync with what actually got compiled. A Cowork-executed compile would need to write these the same way (and interact correctly with `git_publish_wiki()` if the git-publish step also needs to happen) — not designed yet.
3. **Two parallel compile systems.** The likely shape is a **split**: cheap pages stay on the existing Python/API cron (their cost is negligible regardless), expensive/high-value pages move to Cowork. That's real complexity — two prompts to keep behaviorally consistent, two systems that could drift apart, a boundary to define and maintain (which pages route where, and by what rule).
4. **Cowork's actual synthesis prompt** hasn't been authored or tested — need to confirm it can be scoped to reproduce (or improve on) what `compile_wiki.py`'s existing Sonnet prompt produces (footnote citations, section structure, etc. — see the format `write_page()` currently expects).

## Recommended next step

**A single proof-of-concept scheduled task**, scoped to one real page — `AI agents` (the largest, most-tested topic) is the natural choice since its cost and content are already well-characterized from this session's measurements. Verify end-to-end: Cowork can pull the current thought set via the Supabase connector, produce a synthesis of comparable quality to the existing pipeline, and (ideally) write back in a way that's compatible with the existing `wiki_pages` schema — before designing the full split.

## Open questions for the eventual grill-me pass

- Which pages route to Cowork vs. stay on the Python cron — a cost cutoff (e.g. pages over N thoughts), a manually-curated list, or something measured (like the content-creator external-ratio classification used for people)?
- Does Cowork also handle `git_publish_wiki()`'s commit+push step for pages it compiles, or does it write to Supabase only and let the existing Pi cron's git-publish step pick up the change on its next run?
- Does the completion Discord DM (`_build_dm`) need to account for Cowork-compiled pages, or does Cowork's own scheduled-task notification handle that separately?
- Prompt parity: should Cowork's synthesis prompt be a literal port of `compile_wiki.py`'s existing person/topic prompts, or an opportunity to redesign now that cost isn't forcing tradeoffs?

## Related

- `plans/in_progress/wiki_compile_cost_control.md` — the topics/projects any-delta problem this is trying to solve; that file's "Follow-up opened 2026-08-07" section is the diagnosis, this file is the leading candidate fix
- `plans/in_progress/wiki_weekly_cron.md` — the existing Python/API cron this would partially supersede for expensive pages
- `plans/roadmap.md` #7
