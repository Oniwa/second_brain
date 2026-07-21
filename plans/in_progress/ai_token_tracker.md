# AI Token / Cost Tracker — Plan Stub

**Status:** stub — captured 2026-07-20, needs a real planning/scoping session before implementation. This is a sketch of the gap and a rough shape, not a build spec.

**Note:** the first draft of this stub was written from codebase inspection only — it did not check the brain for prior relevant captures. A `get_context` pull after the fact found an entire panned source directly on this topic (see "Grounded in prior captures" below); design should defer to that material, not just this stub's mechanical sketch.

---

## Gap

Six call sites make real LLM/embedding API calls today, and none of them record token counts or cost:

| Call site | Model(s) | Purpose |
|---|---|---|
| `supabase/functions/process-thought/index.ts` | `text-embedding-3-small`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6` (escalation) | Every capture — embedding + classification, on the hot path for every single thought |
| `supabase/functions/generate-embedding/index.ts` | `text-embedding-3-small` | Standalone embedding (re-embeds on edit) |
| `supabase/functions/generate-digest/index.ts` | `claude-sonnet-4-6` | Daily/weekly/review digest generation |
| `scripts/compile_wiki.py` | `claude-sonnet-4-6` | Topic/person/project page synthesis — one call per page, 130+ pages today |
| `scripts/meeting_prep.py` | `claude-haiku-4-5-20251001` | `!prep` meeting briefs |
| `scripts/remind.py` | `claude-haiku-4-5-20251001` | Reminder digest generation |

There is currently **zero cost visibility** anywhere in the system — no per-call logging, no running total, no per-service breakdown. `get_stats` reports thought counts, not spend. The only cost-awareness that exists anywhere in the codebase is a *forward-looking* one: `wiki_implementation.md`'s Phase 2 contradiction-detection design already anticipates needing "a hard cost cap (`--max-cost-usd`, default $5); maintain pricing table; abort if model pricing unknown" — i.e. the next major feature already assumes cost tracking exists, and it doesn't yet.

**Why it matters now, not just later:** the classification cascade (Haiku → Sonnet on confidence < 0.7) and the wiki compiler (one Sonnet call per page, all 130+ pages on `--all`) are exactly the kind of usage pattern that can quietly balloon — "instrument before you optimize" is the same principle that motivated the `get_stats` row-count fix (`mcp_improvements.md` §6). Right now there's no way to answer "did last week's full wiki recompile cost $2 or $20" without checking the Anthropic/OpenAI billing dashboards by hand.

## Grounded in prior captures

You've already panned a source directly on this problem — Nate B. Jones' **"Token Burn Dashboard"** (substack, captured 6/22/2026, `get_context("AI API cost or token usage tracking")`), plus adjacent captures from other sources. Design should incorporate these rather than reinvent:

- **Three-lane fidelity model** (`2d50ee80`) — segregate metrics into *exact counts*, *measured proxies*, and *inferred estimates*, labeled distinctly. This system is in a good position here: real API responses give exact `input_tokens`/`output_tokens`/`total_tokens` for every one of the 6 call sites (§ below), so nothing needs to fall into the "inferred estimate" lane — but the summary UI should still label numbers as exact rather than implying more precision-checking happened than it did.
- **Outcome-tied, not volume-tied** (`7e5c9055`, `ee9541e0`, `4cb2a5e6`) — raw token/cost totals are close to meaningless on their own; "$4.20 on wiki compilation this week" means more paired with "→ 12 pages recompiled" than alone. The `get_stats` cost summary (see below) should report cost *per unit of work* per service (cost/page for `compile_wiki`, cost/capture for `process-thought`, cost/digest for `generate-digest`) rather than bare dollar totals.
- **Avoid the surveillance framing** (`eacf89bd`) — this is a single-user system so the "team dashboard reads as monitoring" failure mode doesn't directly apply, but the spirit still does: frame the summary around "is this system's cost proportional to what it's doing," not a bare spend ticker.
- **Token Optimization / model-selection framework** (`596f9ca9`) — a broader captured idea about comparing model costs and proving ROI via prototyping; relevant if this tracker later grows into "should this call site use Haiku instead of Sonnet" recommendations (out of scope for v1, but the pricing table this stub builds is the prerequisite for that comparison).
- Also relevant: **LLM release-gate cost/latency guardrails** (`da9cb465`, different source) — a hard-budget-as-gate pattern that directly informs the "Alerting/budget" open question below.

## Rough shape of the idea

**Capture, not estimate.** Every API response from Anthropic and OpenAI already includes usage data (`usage.input_tokens`/`usage.output_tokens` for Claude, `usage.total_tokens` for OpenAI embeddings) — no need to estimate from text length.

1. **New table**, e.g. `api_usage_log`: `id, created_at, service (process-thought | generate-digest | compile_wiki | meeting_prep | remind | generate-embedding), model, input_tokens, output_tokens, cost_usd, related_thought_id (nullable)`.
2. **A shared pricing table** (per-model $/1M input, $/1M output) — the same thing the Phase 2 contradiction-detection design already says it needs; building it here means Phase 2 doesn't have to duplicate it.
3. **Each of the 6 call sites logs one row per API call**, fire-and-forget (don't block the primary operation on a logging failure).
4. **Surfacing:** extend `get_stats` with a cost summary (today / 7-day / 30-day / all-time, broken down by service), and/or a new dashboard tile. Not a new MCP tool by default — folding into existing `get_stats` avoids one more tool the agent has to remember to call (same anti-pattern `wiki_routing_and_automemory_bridge.md` §1 is fixing for `get_context`). Per the "outcome-tied" principle above, the per-service breakdown should include a work-unit denominator (pages/captures/digests) alongside the dollar figure, not just a bare total.

## Open questions for a real planning session

- **Migration vs. reuse** — new table (clean, queryable, extensible) vs. append-only log file (simpler, no schema change, harder to query/aggregate). Given every other piece of durable state in this system lives in Supabase, a table is the more consistent choice, but worth deciding deliberately.
- **TypeScript (Edge Functions) + Python (scripts) both need to write rows** — shared logic isn't trivially shareable across the two runtimes. Duplicate the small logging call in both, or route everything through one HTTP endpoint (e.g. Edge Functions write directly, Python scripts POST to a lightweight logging function)?
- **Pricing table maintenance** — hardcoded constants (simple, needs manual updates when Anthropic/OpenAI change pricing) vs. a config file. Given `wiki_implementation.md`'s Phase 2 already flags "abort if model pricing unknown," this decision affects that future feature too — should be made once, shared.
- **Alerting/budget** — is a passive dashboard number enough, or does this want a nudge-style threshold alert (mirrors `scripts/nudge.py`'s pattern) if a day/week/month exceeds some $ threshold? Lean toward passive-only for v1; alerting is a natural v2 if the passive number turns out to matter. If it does, the captured "release-gate" pattern (`da9cb465` — hard token/latency budgets requiring manual approval past a threshold) is a more concrete model than an ad-hoc nudge.
- **Retention** — keep every row forever, or roll up to daily aggregates after some window? Given the volume (one row per capture — potentially thousands/month at current pace), raw-row retention forever may not be necessary once aggregated numbers exist.
- **Backfill** — no historical usage data exists (nothing was logged before this ships), so there's no way to backfill past cost; the tracker only has visibility from its ship date forward. Worth stating explicitly so it's not expected to answer "what has this cost so far this year."

## Files likely touched (not final — scope this in planning)

- New migration: `supabase/migrations/0XX_api_usage_log.sql`
- `supabase/functions/process-thought/index.ts`, `supabase/functions/generate-embedding/index.ts`, `supabase/functions/generate-digest/index.ts` — add logging call after each API response
- `scripts/compile_wiki.py`, `scripts/meeting_prep.py`, `scripts/remind.py` — same
- `mcp/src/server.ts` — extend `getStats()` with a cost summary section
- Possibly `dashboard/index.html` — a cost tile/chart

## Verify (once implemented)

- Trigger one call at each of the 6 sites (a test capture, a manual digest run, a single-topic wiki compile, a meeting prep, a reminder check) and confirm exactly one `api_usage_log` row appears per call with plausible token counts
- `get_stats` cost summary total matches the sum of logged rows for the same window
- Compare a day's logged total against the real Anthropic/OpenAI billing dashboard for that day — should be close (exact match unlikely due to embedding-model pricing rounding, but same order of magnitude)

## Related

- `wiki_implementation.md` Phase 2 (typed edge classifier) — already assumes a pricing table and cost cap exist; this stub is the natural place to build that shared infrastructure first
- `mcp_improvements.md` §6 (`get_stats` 1000-row fix) — same "instrument before you optimize" motivation
