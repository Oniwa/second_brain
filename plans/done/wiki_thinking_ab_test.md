# A/B Test: Adaptive Thinking for Wiki Synthesis

**Status:** not started. Stub written 2026-07-22 after the first `--all` recompile attempt failed and thinking was disabled as the safe default across all 3 Sonnet call sites.

## Context

`compile_wiki.py`, `process-thought`, and `generate-digest` were upgraded from `claude-sonnet-4-6` to `claude-sonnet-5` on 2026-07-22. Sonnet 5 defaults to **adaptive thinking on** when `thinking` is omitted (Sonnet 4.6 defaulted to off) — this silently broke all three call sites, which assumed `content[0]` was always the text block. 19 of 418 wiki pages made real, billed API calls that then failed to parse (~$4 spent, zero output) before the bug was caught. Fixed by (a) explicitly setting `thinking: {"type": "disabled"}` on all 3 call sites and (b) making response parsing robust (scan for the `text`-type block instead of assuming index 0) as defense in depth regardless of the thinking setting.

Disabling thinking was the right call in the moment (mid-recovery from a spend-limit scare, unproven quality benefit, two of the three call sites are recurring/ongoing costs where thinking has no obvious task fit). But it was a safety default, not a tested decision — this plan is to actually test it before locking it in either way.

## Question

Does adaptive thinking measurably improve wiki page quality for `compile_wiki.py`'s synthesis task, enough to justify the extra output-token cost?

**Scope: wiki synthesis only.** `process-thought`'s Sonnet escalation (structured JSON classification of a single thought) and `generate-digest` (templated multi-section fill-in) are recurring/ongoing costs with no clear reasoning benefit — not in scope for this test, stay disabled regardless of the outcome here.

## Test design (not yet run)

1. Add a way to toggle thinking per-run without a permanent code change — either a `--thinking` CLI flag on `compile_wiki.py`, or a temporary local edit reverted after the test. Flag is probably cleaner long-term if the answer turns out to be "sometimes."
2. Pick 1–2 of the largest topics as the test case — "AI agents" (330 thoughts) is the best candidate: most genuine synthesis work (dedup, contradiction resolution, grouping) of any page in the corpus, and the biggest topics are exactly where reasoning would matter most if it matters at all. A small topic (5–10 thoughts) is not a useful test — too little for thinking to change.
3. Compile the same topic twice — once with `thinking: disabled` (current default), once with `thinking: adaptive` — and diff the two outputs for: coherence of synthesis across many thoughts, whether contradictions/near-duplicates are handled better, citation/footnote correctness, and overall structure quality.
4. Check actual cost delta via the API response's `usage` fields (`output_tokens` before/after — thinking tokens bill as output tokens) to get a real per-page cost number, not a guess.
5. Decide: no change (keep disabled everywhere), enable everywhere, or conditionally enable only above some thought-count threshold (e.g. only topics with 50+ thoughts, where the synthesis load is real).

## Not yet decided

- Whether the toggle should be a permanent CLI flag or just a one-off manual edit for the test
- The exact large-topic test candidates beyond "AI agents"
- What threshold, if any, would gate conditional enablement

## Related

- `wiki_weekly_cron.md` — the recompile this decision feeds into; Step 2 (manual full correction) is still pending a successful run
- Today's failed run: 19/418 pages billed and wasted on the parsing bug, 397/418 failed on an unrelated local DNS blip, 1/418 succeeded ("documentation"). Full log was in a scratchpad temp file (not preserved past the session).
