# AI Token / Cost Tracker — Plan Stub

**Status:** stub — captured 2026-07-20, needs a real planning/scoping session before implementation. This is a sketch of the gap and a rough shape, not a build spec.

**Note:** the first draft of this stub was written from codebase inspection only — it did not check the brain for prior relevant captures. A `get_context` pull after the fact found an entire panned source directly on this topic (see "Grounded in prior captures" below); design should defer to that material, not just this stub's mechanical sketch.

**Scope — two phases (merged 2026-07-24).** This plan now covers the whole arc from raw data to human decision, in two phases:
- **Phase 1 — Instrumentation (the data layer)** — the `api_usage_log` table, pricing table, and per-call logging described below. Pure backend plumbing.
- **Phase 2 — Token Burn Dashboard (presentation + review ritual)** — Nate B. Jones' actual "Token Burn Dashboard" framework built on top of Phase 1's data: a fidelity-labeled measurement table, cost-per-work-unit views, Tufte-clean charts, and a `/token-review` weekly-ritual skill. See the dedicated section below. (Phase 2 was briefly split into its own `token_burn_dashboard.md` plan on 2026-07-24, then folded back here — the instrumentation and its payoff are one arc, and keeping them together avoids roadmap fragmentation.)

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

## Phase 1 — Instrumentation: rough shape of the idea

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

---

## Phase 2 — Token Burn Dashboard (presentation + review ritual)

**Depends on Phase 1** (needs `api_usage_log` with real data flowing). This is the payoff layer: Nate B. Jones' **"My Codex Ran 800 Million Tokens in a Day / Token Burn Dashboard"** framework (fully panned into the brain 6/22/2026 — video `https://www.youtube.com/watch?v=l8BloTSLK6M`, Substack `https://natesnewsletter.substack.com/p/token-burn-dashboard`, build guide `https://unlock-ai.natebjones.com/guides/build-your-own-token-burn-dashboard`; brain IDs inline). Phase 1 logs what the *machine* knows; Phase 2 adds the human-judgment layer, the visualization surface, and the recurring review that turns cost rows into behavior change.

### What Nate's framework prescribes (the parts that shape a build)

1. **Three fidelity lanes, never folded** (`2d50ee80`): (a) **Exact** — Codex/Claude Code/raw APIs log to the token; (b) **Measured activity** — a counted proxy (sessions, messages); (c) **Estimate band** — zero-token-count tools (ChatGPT, consumer Claude chat), where the honest move is an agent-reasoned, clearly-*labeled* inferred band, never fake precision (`6b8cc5ca`). **For this system:** all 6 Phase-1 call sites return exact `usage`, so everything is lane (a); lanes (b)/(c) matter only if the dashboard is ever extended to the user's *own* ChatGPT/Claude-chat/Copilot burn outside this repo (see scope-creep question).
2. **Measurement model before visualization** (`3c15c4f4`): a table beats a raw graph — "the graph tells you something happened; the table tells you *what* happened." Fields: `date / tool-or-model / project / job / work type / count-or-activity-or-estimate / fidelity lane / outcome / review burden / next move`. The last four are **human-judgment fields** — exactly what Phase 1's `api_usage_log` deliberately does *not* capture, and the reason Phase 2 exists.
3. **Tufte visualization** (`32aa113c`): the starter kits ship a "Tufte data-display principles as a reusable AI skill" — charts you read and decide from, not glance at. Maps directly onto this environment's `dataviz` skill.
4. **Weekly review ritual** (`d77d3e65`) — the actual point: scan top-usage / quiet / current days, then ask which workstreams produced *accepted* output vs. review burden, where assistant-work was used when computer-work was wanted, and which repeated task should become a workflow / skill / automation next week.
5. **Outcome-tied, not volume-tied** (`7e5c9055`, `ee9541e0`): "$4.20 → 12 wiki pages recompiled" beats "$4.20." Report cost **per unit of work** per service (already a Phase 1 open item).
6. **Single-user caveats** (adapted): the team failure modes (surveillance / leaderboard / cost-panic / vague-adoption, `eacf89bd`) don't apply one-person, but their spirit does — frame around "is this cost proportional to what the system did." **Privacy** (`1880f4c0`): top-usage days expose client/project names; latent here (local/anon-key) but matters if the dashboard is ever shared.

### Rough shape (Phase 2)

1. **Human-judgment annotation store.** `outcome / review burden / next move / work type` can't be auto-derived. Lean toward **capturing the weekly review *as a thought*** (`category: insight`, source `token-review`) rather than a new `usage_review` table — the brain is already the system of record, no new schema, findable by topic later.
2. **Dashboard surface.** Extend the existing local dashboard (`dashboard/index.html` — static HTML, Chart.js, dark theme, anon key) with a **Token Burn** tab: a fidelity-labeled cost table (the measurement model, exact-lane), cost-per-work-unit per service, and a few Tufte-clean charts (daily/weekly burn, per-service split). The *table* is the primary artifact; charts are secondary.
3. **Weekly review skill.** A `/token-review` skill — Haiku-driven, `disable-model-invocation: true`, modeled on `get_pans` — that pulls the week's `api_usage_log` aggregates (a `brain.py --token-usage` flag, mirroring `--pending-pans`), walks Nate's ritual questions, and captures the conclusions back as an `insight`. **Highest-value, lowest-infra part** — it can ship the moment Phase 1 data exists, before any dashboard HTML.

### Phase 2 open questions

- **Annotation store** — capture-as-thoughts (leaning) vs. a `usage_review` table.
- **Dashboard scope** — measurement table only for v1, or table + charts? Which charts actually inform a decision (apply the `dataviz`/Tufte lens)?
- **Ritual trigger** — manual `/token-review` only, or a weekly nudge (mirrors `scripts/nudge.py`, could ride the existing digest)?
- **Scope creep to outside-this-repo usage** — v1 is this system's 6 call sites (all exact-lane); pulling in the user's ChatGPT/Claude-chat/Copilot burn (estimate-band lanes, agent-interview estimation) is a much bigger surface, almost certainly out of scope for v1. Noted so the three-lane model isn't over-built now.

### Phase 2 files likely touched

- `scripts/brain.py` — a `--token-usage`/aggregation flag (deterministic backend for the skill).
- `.claude/commands/token_review.md` — new Haiku-driven review-ritual skill.
- `dashboard/index.html` — new Token Burn tab.
- Possibly a `usage_review` migration *only if* annotation-as-thoughts is rejected.

### Phase 2 verify

- Measurement-table totals reconcile exactly with summed `api_usage_log` rows for the window.
- A `/token-review` run produces a captured `insight` with the ritual's conclusions, findable by topic.
- Cost-per-work-unit figures are sane (cost/page for a known wiki `--all` run ≈ that day's real Anthropic bill, order-of-magnitude).

---

## Related

- `wiki_implementation.md` Phase 2 (typed edge classifier) — already assumes a pricing table and cost cap exist; this stub is the natural place to build that shared infrastructure first
- `mcp_improvements.md` §6 (`get_stats` 1000-row fix) — same "instrument before you optimize" motivation
- `dashboard_improvements_plan.md` — the Phase 2 Token Burn tab is a sibling of the other planned dashboard tabs (audit, People chart, Wiki Pages); could share that work
- `get_pans` skill (`plans/done/get_pans_skill.md`) — the template for the Phase 2 `/token-review` skill (Haiku, `disable-model-invocation`, `brain.py` deterministic backend)
