# Token Burn Dashboard — Plan Stub

**Status:** stub — captured 2026-07-24 from a second-brain pull, needs a real planning/scoping session before implementation. This is the *presentation + review-ritual* layer; it is not standalone.

**Source:** Nate B. Jones — **"My Codex Ran 800 Million Tokens in a Day / Token Burn Dashboard"** (fully panned into the brain 6/22/2026). Video `https://www.youtube.com/watch?v=l8BloTSLK6M`, Substack `https://natesnewsletter.substack.com/p/token-burn-dashboard`, and a step-by-step build guide + starter kits at `https://unlock-ai.natebjones.com/guides/build-your-own-token-burn-dashboard`. Brain thought IDs referenced inline below.

---

## Relationship to `ai_token_tracker.md` (roadmap #3) — read this first

These two plans are **two layers of one system**, and must not be built as rivals:

- **`ai_token_tracker.md` (#3) is the instrumentation/data layer.** It builds the `api_usage_log` table, the shared pricing table, and fire-and-forget logging at all 6 LLM/embedding call sites — capturing the *machine-known* facts of every call (`date, service, model, input_tokens, output_tokens, cost_usd, related_thought_id`). It already grounds itself in this same Nate B. Jones source.
- **This plan is the measurement-model + dashboard + weekly-ritual layer on top of it.** Nate's framework wants fields the machine *cannot* auto-log — `work type / outcome / review burden / next move` — which only a human review produces. This plan adds that human-judgment annotation layer, the dedicated visualization surface, and the recurring review process that turns raw cost rows into "what should become a workflow next week."

**Hard dependency:** this plan cannot start until #3 ships `api_usage_log` with real data flowing. **Decision to make in planning:** build this as a *separate* plan (as written here) or fold it in as **"Phase 2" of `ai_token_tracker.md`**. Leaning separate — the instrumentation is pure backend plumbing while this is UI + a human ritual, a genuinely different kind of work — but the call should be made deliberately, not by default, to avoid the roadmap fragmentation risk.

---

## What Nate's framework actually prescribes

The captured insights, distilled to the parts that shape a build:

1. **Three fidelity lanes, never folded together** (`2d50ee80`): (a) **Exact** — Codex/Claude Code/raw provider APIs log to the token; (b) **Measured activity** — a counted proxy (sessions, messages); (c) **Estimate band** — tools that expose zero token counts (ChatGPT, consumer Claude chat), where the honest move is an agent-reasoned, clearly-*labeled* inferred band, never a fake-precise number (`6b8cc5ca`). **For this system specifically:** all 6 call sites return exact `usage` data, so everything lands in lane (a). Lanes (b)/(c) only matter if the dashboard is ever extended to cover the user's *own* ChatGPT/Claude-chat/Copilot usage outside this repo — which is exactly where Nate's estimate-band machinery earns its keep.
2. **Measurement model before visualization** (`3c15c4f4`): a table beats a raw usage graph — "the graph tells you something happened; the table tells you *what* happened." Minimum fields: `date / tool-or-model / project / job / work type / token-count-or-activity-or-estimate / fidelity lane / outcome / review burden / next move`. Note the last four (`work type, outcome, review burden, next move`) are **human-judgment fields** — this is the layer #3's `api_usage_log` deliberately does not capture.
3. **Tufte visualization skill** (`32aa113c`): the starter kits include an open-source "Tufte data-display principles as a reusable AI skill" — the difference between a chart you glance at and one you actually read and decide from. Relevant to how the dashboard charts are designed (also connects to `dataviz` skill already available in this environment).
4. **Weekly review ritual** (`d77d3e65`) — the actual point of the whole thing: open the chart, scan top-usage / quiet / current days, then ask: which workstreams produced *accepted* output vs. partial work / review burden? Where did I ask for assistant-work when I should have asked for computer-work? Which repeated task should become a workflow / skill / checklist / automation? What did I do manually this week that the computer should carry next week?
5. **Outcome-tied, not volume-tied** (`7e5c9055`, `ee9541e0`): raw token/cost totals are near-meaningless alone — "$4.20 on wiki compilation → 12 pages recompiled" beats "$4.20." Report **cost per unit of work** per service.
6. **Single-user caveats** (adapted): the **team** failure modes (surveillance / leaderboard / cost-panic / vague-adoption, `eacf89bd`) don't apply to a one-person system, but their *spirit* does — frame the dashboard around "is this system's cost proportional to what it's doing," not a bare spend ticker. **Privacy** (`1880f4c0`): top-usage days expose client/project names; keep detail in the private version, scrub before sharing. This system is local-only/anon-key today, so privacy is latent — matters only if the dashboard is ever published.

---

## Rough shape (adapted to this system)

Builds on `api_usage_log` (from #3). Two things this layer adds:

1. **A human-judgment annotation surface.** Nate's `outcome / review burden / next move / work type` fields don't exist in `api_usage_log` and can't be auto-derived. Options to scope: (a) a nullable companion table `usage_review` keyed by day/week that the weekly ritual fills in; (b) reuse the second brain itself — the weekly review *is* a capture (`category: insight`, source `token-review`), so the "annotation store" is just thoughts, queried back by topic. Option (b) is very on-brand (the brain is already the system of record) and avoids new schema — lean toward it.
2. **A dashboard surface.** Extend the existing local dashboard (`dashboard/index.html` — static HTML, Chart.js, dark theme, anon key) with a **Token Burn** tab/section rather than a new app: a fidelity-labeled cost table (the measurement model, exact-lane), cost-per-work-unit per service, and a small set of Tufte-clean charts (daily/weekly burn, per-service split). The measurement *table* is the primary artifact; charts are secondary (per principle #2).
3. **A weekly review ritual, as a skill.** A `/token-review` (or `token_review`) skill, Haiku-driven and `disable-model-invocation: true` like `get_pans`, that pulls the week's `api_usage_log` aggregates (via a `brain.py` flag, mirroring `--pending-pans`), walks the user through Nate's ritual questions, and captures the conclusions back into the brain as an `insight`. This is the piece that turns a passive number into a recurring behavior change — and it's the highest-value, lowest-infra part.

**Sequencing hint:** the review-ritual skill (#3 above) can ship the moment `api_usage_log` exists, *before* any dashboard HTML — a table + a skill delivers most of Nate's value; the charts are polish.

## Open questions for a real planning session

- **Separate plan vs. Phase 2 of `ai_token_tracker.md`** — decide first (see relationship section).
- **Annotation store** — new `usage_review` table vs. capture-as-thoughts (lean thoughts).
- **Dashboard scope** — measurement table only for v1, or table + charts? Which charts actually inform a decision vs. just look good (apply the Tufte/`dataviz` lens)?
- **Ritual cadence & trigger** — manual `/token-review` only, or a weekly nudge (mirrors `scripts/nudge.py`) that prompts the review? Could ride the existing digest.
- **Scope creep to outside-this-repo usage** — v1 covers only this system's 6 call sites (all exact-lane). Do we ever want to pull in the user's ChatGPT/Claude-chat/Copilot burn (the estimate-band lanes)? That's where Nate's agent-interview estimation applies, but it's a much bigger surface — almost certainly out of scope for v1, noted so the three-lane model isn't over-built now.

## Files likely touched (not final — scope in planning)

- Depends on `ai_token_tracker.md`'s `api_usage_log` migration + pricing table (prerequisite).
- `scripts/brain.py` — a `--token-usage`/aggregation flag (deterministic backend for the skill, mirrors `--pending-pans`).
- `.claude/commands/token_review.md` — new Haiku-driven review-ritual skill (`disable-model-invocation: true`).
- `dashboard/index.html` — new Token Burn tab (measurement table + Tufte-clean charts).
- Possibly a `usage_review` migration *only if* the annotation-as-thoughts approach is rejected.

## Verify (once implemented)

- The measurement table's totals reconcile exactly with summed `api_usage_log` rows for the same window (same check `ai_token_tracker.md` already specifies).
- A `/token-review` run produces a captured `insight` thought with the ritual's conclusions, findable later by topic.
- Cost-per-work-unit figures are sane (e.g. cost/page for a known wiki `--all` run matches the real Anthropic bill for that day, order-of-magnitude).

## Related

- **`ai_token_tracker.md` (#3)** — the prerequisite instrumentation layer; this plan is its payoff. Same Nate B. Jones source.
- `dashboard_improvements_plan.md` (#6/#7) — the Token Burn tab is a sibling of the other planned dashboard tabs (audit, People chart, Wiki Pages); could share that work.
- `get_pans` skill (`plans/done/get_pans_skill.md`) — the template for the review-ritual skill (Haiku, `disable-model-invocation`, `brain.py` deterministic backend).
- `dataviz` / Tufte — the environment's `dataviz` skill covers the chart-design principle Nate packages as his "Tufte skill."
