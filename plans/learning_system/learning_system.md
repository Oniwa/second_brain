# Learning system — a `/learn` skill for closing applied AI/agentic-systems gaps

_Filed 2026-09-18._ Driven by `applied_ai_agentic_systems_knowledge_assessment.md` (copied into this
directory) — a third-party knowledge assessment scoring the user 19.5/30 on applied generative
Artificial Intelligence (AI) and agentic systems, and naming a specific, ranked topic backlog to close.
The assessment is the actual
learning target; this plan is the design for the skill that will be used to work through it.

**Origin note:** the specific spark for wanting a system built around this, rather than just using
Claude ad hoc, was one concrete takeaway from panning Austin Marchese's self-education video: his
three-step "learning ladder" (ELI5/12/18 → why this matters to me → ground it in what I'm working on —
second-brain thought `159e464a`). That ladder is now the explanation step of Mode 2 (see the build
sequence below) — it's not just background inspiration, it's load-bearing in the design.

## Why a custom skill, not an off-the-shelf one

Two existing methodologies were evaluated in depth (full comparison in session history, not reproduced
here):

- **Austin Marchese's six-question self-education framework** — a single-pass, Return on Investment
  (ROI)-gated triage: why
  learn it, what depth is needed, who's solved it (alpha farming), make it concrete (smallest V1 +
  teach-back), apply it to your actual situation, keep learning (recursive). Optimized for *acquiring*
  useful knowledge fast, one constraint at a time.
- **Matt Pocock's `/teach` skill** — a stateful, multi-session tutoring loop (mission file, Zone of
  Proximal Development (ZPD)-scoped
  lessons, spaced-repetition warm-ups, persistent learning records). Optimized for *retaining* a domain
  over months.

Neither fits as-is. The user's second-brain history shows a builder/architect/evaluator pattern (learn →
build → evaluate → deepen only if ROI holds), not a "spend six months mastering one domain" pattern —
closer to Marchese. But the assessment gaps (Retrieval-Augmented Generation (RAG), AI evaluation,
observability, failure analysis) are
exactly the kind of technical depth that decays without reinforcement — where Pocock's retention
mechanisms earn their keep. The user's actual job (Software Verification Engineer) also demands a
mandatory failure-analysis/verification gate that neither framework has natively.

**Converged design:** a lean, mode-based router, not a single pipeline and not a symmetrical blend.
Marchese governs admission *and* periodic continuation/scope checks (not just a one-time gate — topic
gravity resumes mid-mission, e.g. RAG → GraphRAG → benchmarking five vector DBs). Pocock's mechanisms
(persistent state, spaced retrieval, ZPD) are borrowed selectively, only for topics that clear the bar for
sustained mastery. A failure-analysis + verification step is promoted to a mandatory gate for any
professionally-actionable topic, reflecting the user's actual job discipline.

An independent Opus 5 review (adversarial, not just confirming consensus) flagged two contradictions
and several simplifications, incorporated into the build plan below — see "Fixes from review."

## The three modes (target architecture — not all built at once)

```
Learning request
    |
1. Relevance gate (why learn this? professionally actionable / capability-building / curious)
    |
2. Competency target (awareness / practitioner / independent practitioner / architect)
    |
3. Select mode
    +-- Mode 1: Quick explanation      (awareness, no durable capability needed)
    +-- Mode 2: Focused learning cycle (bounded problem, practitioner depth, build/decide soon)
    +-- Mode 3: Stateful mastery track (strategic gap, sustained reuse, retention matters)
```

### Competency levels — what each target actually means

Named repeatedly above but not previously defined anywhere in this doc. Observable distinctions, not
vibes:

- **Awareness** — can explain the concept and recognize when it applies, in conversation. Cannot build
  or troubleshoot anything with it. No implementation expected. This is Mode 1's ceiling.
- **Practitioner** — can implement a bounded solution *with guidance* (this skill, docs, examples).
  Can't yet troubleshoot novel failures alone or defend a design choice against alternatives. Default
  target for Mode 2 when nothing else is specified.
- **Independent practitioner** — can implement *and* troubleshoot without step-by-step assistance;
  knows the common failure modes going in, not just after hitting them. The bar most Mode 2 missions
  should realistically aim for if they run long enough to include real failure analysis.
- **Architect** — can select between competing designs and defend the tradeoffs (cost, latency,
  complexity, risk) for a specific situation, not just describe how each option works. Requires having
  seen or built more than one approach — usually needs Mode 3's sustained exposure, not a single Mode 2
  cycle.

A mission can state a *target* competency higher than what one session will reach — the learning record
in that case should say so explicitly rather than silently overstating what was demonstrated.

Cross-cutting non-negotiables for Modes 2 and 3 (professionally actionable topics only):
mission relevance, smallest practical application, teach-back, failure analysis, verification evidence.

## Build sequence — build the leanest useful version first, earn complexity through real use

**v0.1 — Mode 2 only.** One skill answering: *"How do I acquire enough verified understanding of a
professionally relevant topic to apply it correctly?"* No router, no quick path, no mastery track, no
spaced-repetition ledger, no evidence-classification schema. (Multi-source grounding — second brain *and*
live external research — is in scope from v0.1; it's not part of the deferred second-brain integration,
it's how the skill avoids being limited to only what's already been captured.)

**v0.1 eligibility (resolved — flagged as inconsistent by the GPT 5.6 Sol review):** Mode 2 accepts a
request when a bounded applied exercise can be named for it — this covers both **professionally
actionable** topics (tied to a current/near-term responsibility) and **capability-building** topics
(closes an identified gap, no immediate deliverable, but still supports a real exercise). **Curiosity-only**
requests (no planned application, nothing to build or decide) are declined in v0.1 with an explicit
message — "This sounds like Mode 1 (quick explanation), which isn't built yet; want to give it a bounded
application instead, or just ask me directly?" — rather than silently run through the full cycle anyway.
The cross-cutting non-negotiables (failure analysis, verification evidence) apply to **both** accepted
categories, not just professionally actionable ones — a capability-building mission still has to survive
contact with "how would this fail, how would you test it," it just doesn't have an immediate deliverable
forcing the question.

### v0.1 interaction state machine (literal, not prose guidance)

Each step below has an exact opening move, exact fields, and an exact transition/exit rule — added
because "infer from the stated decision rather than asking cold" was previously guidance, not gate logic,
and a fresh build would have invented these differently every time.

**Step 1 — Mission + depth.**
- Opening question (single turn, not a multi-question form): *"What are you trying to learn, and what
  decision or thing you're building does it support?"*
- Required before Step 2: `topic` (string) and `application` (what decision/build depends on it — may be
  "just curious," which triggers the eligibility decline above).
- `target_competency`: infer from the stated application if a competency level is implied (e.g. "I need
  to decide whether to add X" → practitioner/independent practitioner; "I need to defend this design
  choice to my team" → architect); otherwise **default to practitioner** without asking. Never ask the
  user to pick from the four-level list cold — that's an implementation detail of this skill, not
  something the user should have to know unprompted.
- Exit: if the user gives only a bare topic with no application ("teach me reranking"), ask the Step 1
  question once more, specifically for the missing `application` field, before proceeding. Do not proceed
  to Step 2 without `application` filled in (even if it's "just curious," which then triggers the decline
  above).
- Once `topic` + `application` + `target_competency` are set, state the normalized mission back in one
  sentence (e.g. *"Mission: determine whether adding a reranker is worth it for your RAG prototype,
  targeting independent-practitioner depth."*) and proceed directly into Step 2 — no separate approval
  round-trip required unless the user objects to the restated mission.

**Step 2 — Grounded explanation.** See "Sourcing and grounding contract" below for the exact tool
sequence; this step's *output* structure is: run the three-step learning ladder (see "Learning ladder —
exact output shape" below), then a short grounding note listing what came from the second brain vs. live
research (feeds `SOURCES.md`).

**Step 3 — Applied exercise.** See "Applied-exercise contract" below.

**Step 4 — Teach-back + completion gate.** See "Decision definitions and generic rubric rule" below.

**Step 5 — Learning record + next step.** Write `RECORD.md` (template below) and state one of
`continue` / `apply` / `pause` / `graduate` (defined below) as the session's outcome, with a one-line
reason.

**"I just need the answer" exit (any step):** if the user says this explicitly, stop teaching, give the
plain answer/explanation directly, skip teach-back and the completion gate, and write a `RECORD.md` that
says so plainly (outcome: `paused`, reason: "user requested direct answer, not a verified cycle") rather
than fabricating a passed gate. This is a legitimate exit, not a failure state.


**v0.2 — after several real uses.** Improve friction points found in practice; add the evidence
classification schema (see fixes below — deferred here deliberately, not because it's optional forever);
add richer continue/pause/graduate *state management* (multi-session history, re-opening a paused topic)
— the four outcomes themselves are already defined in v0.1 below, since `graduate` already has a
real side effect (second-brain capture) that can't be deferred; refine the learning-record structure
based on what v0.1 actually needed.

**v0.3 — only after Mode 2 proves useful.** Add Mode 1 (quick explanation) and the routing shell that
dispatches between modes based on the relevance-gate + competency-target answers.

**v1.0 — only when a topic clearly requires sustained mastery.** Add Mode 3: persistent mission
workspace, spaced retrieval, ZPD-scoped lessons, deeper mastery records, scheduled reassessment (the
Pocock mechanisms, now earned rather than assumed).

## Learning ladder — exact output shape

Resolves an ambiguity the GPT 5.6 Sol review correctly flagged: "explain it like I'm 5/12/18" does
**not** mean producing three redundant explanations at three ages, and the "sequence" referred to is
simplify → why it matters → ground in my situation, not 5 → 12 → 18. The actual output for Step 2 is
exactly three short parts, in this order, with no more than one explanation per part:

1. **Simple model** — one short analogy or plain-language explanation, at whatever single age-level
   depth actually fits the concept and the user's stated familiarity (the skill picks one level, it
   doesn't ask which of 5/12/18, and doesn't produce more than one). A domain analogy the user already
   knows (sports, cooking, whatever fits the concept) is a valid substitute for a literal "like I'm 5"
   framing, not an additional fourth part.
2. **Why it matters here** — one paragraph tying the concept directly to the mission from Step 1, not a
   generic "this is important because..." statement.
3. **Concrete mapping** — one paragraph mapping the concept onto the user's actual system, decision, or
   artifact (asking a clarifying question first if that context wasn't given in Step 1).

Multiple age-level explanations are only produced if the user explicitly asks for a different depth after
seeing part 1 — never proactively.

## Decision definitions and generic rubric rule

The GPT 5.6 Sol review correctly found these conflated into one vague "completion gate" — worth keeping
distinct even in v0.1, since the pilot's own worked example shows what happens if they aren't (a 3-point
teach-back rubric can pass while a 6-point competency contract and the mandatory failure-analysis gate
are still unmet). Five separate decisions, evaluated at Step 4/5:

- **Teach-back passed** — the user's own words (not the model's) satisfy the rubric written in Step 2
  (see the generic rubric rule below). This is a necessary but not sufficient condition for anything else
  on this list.
- **Exercise verified** — the Step 3 applied exercise produced the observable output/decision defined in
  its exercise contract (see "Applied-exercise contract" below) — e.g., the comparison actually ran and
  produced a result, not just that code was written.
- **Failure-analysis satisfied** — the user named at least two concrete failure modes for the concept
  (not generic ones) and how each would be detected — this is the mandatory gate from the "Why a custom
  skill" section, evaluated here explicitly rather than assumed to happen inside teach-back.
- **Mission completed** — teach-back passed **and** exercise verified **and** failure-analysis satisfied.
  This is the bar for a normal, successful v0.1 session — not the same thing as "graduated."
- **Graduated** — every item in the competency contract (see below) is separately checked off, not just
  "mission completed." A mission can be `completed` without being `graduated` (e.g., independent
  practitioner-level contract items remain outstanding even though this session's narrower mission was
  satisfied) — the learning record must say which is true, not conflate them.

**Generic rubric-construction rule** (used to write both the teach-back rubric and the competency
contract for *any* topic, not just the pilot's pre-written example): a rubric must cover, at minimum:
1. The core mechanism (what the concept actually does).
2. Mission-specific relevance (why *this* mission needs it, not textbook importance).
3. At least one tradeoff or boundary condition (when this concept is *not* the right call).
4. At least two concrete, non-generic failure modes.
5. How each of those failure modes would be detected/tested.
6. How success would be measured for the stated mission.

Write this rubric during Step 2 (before teaching), state it to the user verbatim at Step 4 grading time,
and grade only against it — never expand or shrink criteria after the fact.

**Remediation path (unchanged from the Opus 5 review, restated here since it's part of this same gate):**
on a miss, name the specific unmet criterion, re-teach only that part, retry once; on a second miss, log
it as a Remaining Gap in `RECORD.md` and end the session — don't loop indefinitely. Scaffolding, coaching,
and debugging the user's own exercise attempt is allowed and expected; the one bright line is never
supplying the teach-back's own answer in the user's place, even if asked twice — offer the plain
explanation and end the cycle instead of quietly filling in their teach-back for them.

## Applied-exercise contract (Step 3)

Resolves the previously unspecified "smallest useful implementation or decision exercise." Every
exercise, regardless of topic, is scoped by naming these fields up front (part of the Step 2 → Step 3
transition, stated to the user before starting):

- **Type** — coding exercise (something is built/run) or decision exercise (a real comparison/analysis
  produces a recommendation) — chosen based on whether the mission's `application` from Step 1 is a
  build or a decision. RAG reranking is a decision exercise (compare with/without reranker); learning a
  new tool's API might be a coding exercise (build the smallest thing that calls it).
- **Timebox** — default 30–45 minutes of the ~60-minute session envelope; state it up front so scope stays
  bounded.
- **Baseline/control** — what "without the concept" looks like, when the exercise is a comparison (e.g.
  retrieval quality without a reranker, as the control for retrieval quality with one).
- **Observable output** — the concrete artifact or result that will exist when the exercise is done (a
  yes/no recommendation with supporting numbers; a small script that runs; a written comparison) — this
  is what "exercise verified" above checks against.
- **Blocked-exercise fallback** — if a prerequisite is missing (no dataset, no credentials, a dependency
  won't install) inside the timebox, downgrade to the smallest exercise that's still actually runnable
  with what's available, note the downgrade in `RECORD.md`, and don't stall the session trying to fix
  the environment.

The skill may scaffold starter code, explain unfamiliar syntax, and help debug the user's own attempt —
none of that violates "don't complete the user's thinking"; only producing the exercise's *conclusion* or
the teach-back's *answer* on the user's behalf does.

## Sourcing and grounding contract (Step 2)

Resolves the previously unspecified tool-call sequence. Step 2 always runs, in this order:

1. Call `get_context` (or `semantic_search` if `get_context` returns nothing relevant) with the
   normalized mission from Step 1 — surfaces prior second-brain captures and saved beliefs.
2. Run live external research (web search/fetch) targeting, at minimum: one primary/official source
   (docs, spec, paper) and one practitioner source (a real implementer or maintainer, per "alpha
   farming" — not a generic influencer roundup). A third evaluation/failure-analysis source is added
   when the topic backlog's failure-analysis gate needs it.
3. Merge into a short grounding note (feeds `SOURCES.md`): each claim used in the ladder explanation is
   tagged with where it came from — second brain vs. freshly researched — per the "never
   second-brain-only" requirement above.
4. **If sources disagree, or nothing authoritative turns up:** state the disagreement/gap plainly to the
   user, downgrade the mission's expected outcome to "needs experiment" instead of a confident answer,
   and proceed to Step 3 anyway rather than stalling (this was Opus 5 review fix #7 — restated here with
   the actual mechanism, not just the principle).
5. **If second-brain MCP tools are unavailable** (the skill's `compatibility` frontmatter names them but
   they're unreachable at runtime): proceed on live external research alone, note the degraded grounding
   in `SOURCES.md`, and do not block the session — second-brain grounding is valuable, not mandatory
   infrastructure.

## Fixes from the Opus 5 review (apply before/while building v0.1)

Two real contradictions, plus simplifications — all reduce scope, none add it. (A second, independent
adversarial review by GPT 5.6 Sol found further gaps beyond this list — those are called out inline below
where they extend an existing fix, and covered by the new sections above and the "Artifact storage"
rewrite below.)

1. **Evidence classification is a principle in v0.1, not a schema.** It was declared a "hard requirement
   from the first version" while also being deferred to v0.2 in the build sequence — pick one. v0.1
   keeps only the *principle* ("when citing saved second-brain notes, name it as a saved belief and ask
   for confirmation, don't silently assume it"). The full six-field schema
   (`statement`/`classification`/`source`/`captured_at`/`confidence`/`override_allowed`) is v0.2 work.
2. **Completion gate needs a remediation path, not just pass/fail.** On a miss: name the specific gap,
   re-teach only that, retry once; on a second miss, log it as a Remaining Gap and end the session
   anyway (don't loop indefinitely). Add an honest "I just need the answer" exit that ends the session
   without faking a teach-back — for a personal skill, abandonment is the dominant failure mode, not
   shallowness. **Expanded:** see "Decision definitions and generic rubric rule" above — a second,
   independent review (GPT 5.6 Sol) found this single "completion gate" was actually conflating five
   different decisions (teach-back passed / exercise verified / failure-analysis satisfied / mission
   completed / graduated), which is now resolved there.
3. **Self-grading has no independent check.** Same model teaches and evaluates. Mitigate, don't solve:
   write the rubric *before* teaching and restate it verbatim at grading time; require the user's answer
   in their own words before any model commentary; make "don't complete the user's thinking" a rule about
   one observable behavior (never supply the exercise's answer even if asked twice — offer the plain
   explanation and end instead).
4. **Cut v0.1 to 5 steps, not 10.** Steps 1–4 of the original draft collapse into one exchange;
   "assess current understanding" is inferred from the teach-back, not asked upfront. The 5 steps are
   still the visible shape of a session; the "v0.1 interaction state machine" section above adds the
   exact mechanics inside each step without adding new user-facing steps.
5. **Pilot success criteria must be falsifiable, not a 10-item subjective checklist.** See below.
6. **Define state-file location and resume protocol now**, not as an afterthought — cheap to specify
   up front, expensive to retrofit once records exist. **Resolved:** see "Artifact storage" section below
   — a sibling `learning_lab` project, identified by its repo (not a hardcoded path), so it stays
   reachable from any device that can clone/pull it, not just the one where it was first created. A
   second review (GPT 5.6 Sol) found the *protocol* underneath that identity (clone discovery, dirty-tree
   handling, commit/push timing) was still unspecified — resolved by simplifying v0.1's scope; see
   "Artifact storage" below.
7. **No failure branch specified for stale/conflicting/absent sources** in step 2 — the skill should
   state the disagreement, downgrade the outcome to "needs experiment," and proceed rather than stalling.
   **Resolved:** see "Sourcing and grounding contract" above, item 4.

## Pilot

**Topic:** RAG reranking evaluation — directly closes the #1-ranked gap in the assessment (RAG scored
0.5/3, the clearest gap; RAG is also ranked #1 in the assessment's own "Highest-Value Learning
Priorities").

**Mission (narrowed to be falsifiable, not an open-ended study):** "Determine whether adding a reranker
improves retrieval quality enough to justify its latency, cost, and complexity for a small RAG
implementation."

**Worked example — competency contract and rubric.** Referenced above and by Opus 5 review fix #3, but
never previously illustrated. For this pilot mission, target competency = **independent practitioner**
(per the levels just defined: can implement and troubleshoot a reranking decision without step-by-step
help, going in aware of the common failure modes).

*Competency contract* (`MISSION.md`'s graduation criteria — "I can..." statements, observable, not vague):
1. Explain what a reranker adds on top of a base retriever, in one paragraph, unprompted.
2. Implement a reranking step in a small retrieval pipeline.
3. Design a retrieval-quality comparison (with vs. without reranker) using a repeatable small dataset.
4. State the latency/cost/complexity cost of adding it.
5. Give a specific yes/no recommendation for the stated use case, with the evidence that supports it.
6. Name at least two ways a reranker itself can fail or mislead (e.g., overfit to the eval set, hides a
   bad base-retrieval result instead of fixing it).

*Rubric* (written before teaching, restated verbatim at grading time, per fix #3, and now aligned with
the "Decision definitions and generic rubric rule" section above rather than treated as one conflated
gate). This mission has three separate checks, not one:
- **Teach-back passed** — the user's own words (not the model's) cover: (a) what reranking does
  differently from initial retrieval, (b) why it costs something (latency/compute/complexity), and
  (c) at least one concrete scenario where skipping it would still be the right call. This checks
  competency-contract items 1 and 4–5; it does **not** by itself satisfy items 2–3 or 6.
- **Exercise verified** — the reranking step from competency-contract item 2 actually runs against the
  small dataset from item 3, and produces the with/without comparison named in the applied-exercise
  contract above (not just "I wrote the code").
- **Failure-analysis satisfied** — competency-contract item 6 is its own independent check: at least two
  concrete ways a reranker can fail or mislead, each with a way to detect it — checked separately so a
  clean teach-back can't stand in for it.

Partial/vague answers on any one of the three checks trigger the remediation path (name the gap, re-teach
only that part, retry once, then log as a Remaining Gap) — a Remaining Gap on one check doesn't block the
other two from passing; **mission completed** requires all three, and **graduated** additionally requires
the user affirms the full competency contract (all 6 items) holds, per the generic rubric rule.

**Pilot success criteria (3, not 10):**
1. Did the session end with a defensible yes/no on the reranker?
2. Did it fit one sitting (~60 minutes)?
3. Did the user voluntarily start a second topic within two weeks? (If not, v0.2 should *subtract*
   process, not add it.) **Note:** unlike criteria 1–2, this one isn't skill-enforced or checkable from
   any artifact — it's a manually-observed judgment call the user makes about their own follow-through,
   not something `.github/skills/learn/SKILL.md` can verify itself.

## Topic backlog (from the assessment, ranked by the assessment's own priority ordering)

1. **Retrieval-Augmented Generation & retrieval architecture** — largest gap (0.5/3 on RAG failure
   analysis). Embeddings, chunking, hybrid search, reranking, retrieval vs. answer evaluation, GraphRAG.
2. **Hybrid local/cloud Large Language Model (LLM) architectures** — aligns with existing
   Python/Docker/privacy interests.
   Local inference (Ollama/LM Studio/vLLM), quantization tradeoffs, privacy-aware routing, cloud
   fallback.
3. **AI evaluation & quality engineering** — builds directly on existing verification-engineer
   background; likely differentiating specialty. Golden datasets, LLM-as-judge, regression testing,
   quality-cost-latency tradeoffs.
4. **Agent observability & production operations** — traces/spans, token/cost attribution, semantic
   error taxonomies, drift detection.
5. **Tool orchestration & workflow-control patterns** — already a relative strength (2.5/3 on
   multi-agent, workflow architecture); formalize the vocabulary (ReAct, planner-executor,
   router-worker, state machines, idempotency).
6. **Advanced memory systems** — most valuable after retrieval fundamentals land; memory write
   policies, consolidation, contradiction resolution, provenance (notably: preventing "self-reinforcing
   profiles," the same concern already built into this skill's own evidence-classification design).
7. **Targeted LLM foundations & model engineering** — architectural-level understanding (tokenization,
   attention, quantization, fine-tuning justification) in service of decisions, not research depth.

Cross-cutting gaps threaded through the mandatory failure-analysis gate rather than treated as separate
topics: formal tool/model routing decision frameworks (authority, freshness, confidence, permissions,
cost, escalation) and AI-native production failure analysis (silent semantic failures: bad retrieval,
plausible-but-wrong plans, proxy-metric gaming, stale memory, prompt injection).

## Skill format — agentskills.io Agent Skills spec

This skill ships as an **Agent Skills**-format skill (agentskills.io), matching the repo's existing
`.github/skills/pick-up/SKILL.md` — not the `.claude/commands/*.md` slash-command style used by
`pan`/`synth`/`recap`/`grill-me`. Concretely:

```
.github/skills/learn/
├── SKILL.md          # required: YAML frontmatter (name, description, ...) + Markdown instructions
├── scripts/           # optional: e.g. a state-file read/write helper if needed
├── references/         # optional: e.g. the full mode-1/3 design, deferred until v0.3/v1.0
└── assets/             # optional: e.g. the learning-record template
```

Frontmatter requirements per spec: `name` (lowercase, hyphens, matches directory name — `learn`),
`description` (what it does + when to use it, specific enough to trigger reliably — e.g. "Run a focused,
verified learning cycle on a professionally relevant technical topic, producing a working exercise and a
concise learning record. Use when the user wants to learn/study/get up to speed on an AI, agentic-systems,
or technical topic they intend to apply."), optionally `compatibility` if the skill assumes second-brain
Model Context Protocol (MCP) tools are available. Keep `SKILL.md` itself lean (per agentskills.io best
practices — comparable to
this repo's own "under 200 lines, defer depth to reference files" belief already captured in the second
brain) — v0.1's 5-step Mode 2 flow should fit directly in `SKILL.md`; Mode 1/Mode 3 additions in v0.3/v1.0
belong in `references/` until promoted.

Note: cross-tool parity between `.claude/commands` and `.github/skills` formats is already a tracked
backlog item (`plans/in_progress/cross_tool_skill_sync.md`); this skill launches in Agent Skills format
only, consistent with `pick-up`, and can be back-ported to a `.claude/commands` version later if that
backlog item generalizes the sync.

## Artifact storage — a separate project directory, not inside `second_brain`

**Decision: learning artifacts (mission files, sourced material, exercises, learning records, review
ledgers) live in a new sibling project, not inside this repo — identified as its own git repo, not a
fixed local path.** This distinction matters beyond tidiness: a bare local folder only exists on one
machine, but a git repo is clonable/pullable/pushable from anywhere with git and auth — including a
mobile Claude Code session that has no access to an arbitrary desktop filesystem path. Repo name/URL
still need to be confirmed before v0.1 (see Open decisions), but the identity model (repo, not path) is
settled.

**v0.1 storage protocol — deliberately simplified (resolved per the GPT 5.6 Sol review):** the review
correctly found that "clone by identity, discover existing clones, commit and push at natural
checkpoints" was a full remote-git-automation protocol with no answers for dirty trees, push failures,
merge conflicts, or offline use — too much infrastructure for a first pilot that's supposed to test the
5-step pedagogy, not a sync system. **v0.1 requires a pre-cloned local `learning_lab` at a path the user
confirms once** (e.g. an environment variable or a value recorded once in the skill's own notes) — the
skill does **not** clone, discover multiple candidate clones, or push automatically in v0.1:
1. If the confirmed local path doesn't exist or isn't a git repo, stop and ask the user to clone it
   there first — don't attempt to `git clone`/create it automatically.
2. Read/write files directly under `<learning_lab_path>/<topic-slug>/`.
3. After writing `RECORD.md` (Step 5) or a `Graduate` outcome, run a local `git add` + `git commit` in
   that repo (commit message: the topic slug + outcome, e.g. `"rag-reranking-evaluation: completed"`) —
   **local commit only, no push.** Tell the user the commit happened and that pushing/syncing
   `learning_lab` elsewhere is a manual step on their side.
4. If the local git repo has uncommitted, unrelated changes already sitting in it (a dirty tree not
   caused by this skill), stop and tell the user rather than committing over them.

Full remote automation (clone-by-URL discovery, pull-before-read, push, conflict/failure handling) is
**deferred to v0.2+**, once the pre-cloned-local model has actually been used and its friction points are
known — this is the same "earn complexity through real use" discipline the rest of v0.1 already follows,
applied to storage instead of pedagogy. The repo-identity decision itself doesn't need to be revisited
when that happens; only the automation built on top of it does.

**Why not inside `second_brain`:**
- **Different artifact shape, different lifecycle.** Second brain's core data model is one atomic,
  immutable captured thought at a time, compiled into wiki pages — a stable, append-mostly history.
  Learning artifacts are the opposite: multi-file working documents that get *edited in place* across a
  session and across weeks (a mission file, a growing lesson log, an evolving review ledger, actual
  built code from the "smallest useful exercise" step). Mixing a mutating working-scratch tree into a
  repo whose other content is meant to be a durable, mostly-append history creates git-history noise and
  blurs a distinction this project already draws elsewhere (`open_pans.md` is explicitly a disposable
  regenerated view, not the durable record — the database is). Learning artifacts are the opposite case:
  they're the primary durable record for that topic, not a disposable view of something else.
- **Code exercises don't belong in a personal-knowledge-management repo.** "Build the smallest useful
  project" produces real runnable code, possibly with its own dependencies/venv per topic. That's a
  project workspace concern, not a knowledge-capture concern.
- **Room to grow without crowding `second_brain`'s directory listing**, which already spans
  `mcp/`, `supabase/`, `discord/`, `dashboard/`, `scripts/`, `pans/`, `pocket_transcripts/`, `plans/`,
  `resources/`, `compiled_wiki/`. A per-topic learning tree is a distinct enough concern to earn its own
  root, same reasoning already applied to `compiled_wiki` being split into its own mirrored repo.
- **Precedent already exists in this environment** for a skill hosted in one project reading/writing
  files in a sibling project directory — the `/transcript` skill (hosted here, in
  `.claude/commands/transcript.md`) already writes its output to `C:\projects\youtube_transcript\`, a
  separate project. The learning skill (hosted in `second_brain/.github/skills/learn/`) writing to
  `learning_lab/` is the same pattern, not a new one — but resolved by repo identity rather than a
  hardcoded path, per the mobile-access reasoning above (even though v0.1 itself only reads/writes a
  pre-cloned local copy, not the remote).

**Proposed structure (per topic, git-tracked in its own repo, pre-cloned locally for v0.1):**

```
learning_lab/
├── README.md                      # index of topics + status (mirrors CURRENT.md's role)
└── <topic-slug>/                  # e.g. rag-reranking-evaluation/
    ├── MISSION.md                 # mission statement, target competency, competency contract
    ├── SOURCES.md                 # curated authoritative sources (second-brain + live external research
    │                               #   — see the grounding step above; explicitly not second-brain-only)
    ├── lessons/                    # session-by-session lesson content
    ├── exercises/                 # actual code from the "smallest useful exercise" step
    ├── RECORD.md                  # the learning-record output (mirrors the template in this plan)
    └── REVIEW.md                  # spaced-repetition ledger — Mode 3 / mastery-track topics only
```

**Resume behavior in v0.1 (resolved — GPT 5.6 Sol flagged this as incomplete despite being called
"resolved"):** v0.1 supports single-sitting missions plus exact-slug resume only — no fuzzy topic
matching, no "what was I working on" inference. To resume, the user names the topic-slug (or the skill
asks for it if the request is ambiguous, e.g. "continue my RAG work" when multiple RAG-adjacent slugs
exist); the skill then reads `MISSION.md` + `RECORD.md` for that exact slug before continuing. Reopening
a topic already marked `graduate` starts a **new**, explicitly-named follow-on mission (its own slug),
not a silent re-edit of the graduated one. Richer resume mechanics (partial-session recovery, fuzzy
matching, mission-drift reconciliation) are v0.2+ work, once real resume patterns are observed.

### Artifact templates (resolved — these were referenced above but never actually defined)

**`<topic-slug>/MISSION.md`** — written at the end of Step 1:
```markdown
# Mission: <topic title>

- **Slug:** <topic-slug>
- **Started:** <date>
- **Mode:** 2 (professionally-actionable / capability-building)
- **Target competency level:** <awareness | practitioner | independent practitioner | architect>
- **Bounded exercise (named at admission):** <one sentence — what will actually get built/run/measured>

## Competency contract
By the end of this mission I can:
1. <"I can ..." statement>
2. <"I can ..." statement>
3. <"I can ..." statement>
(3–6 statements; see "Decision definitions and generic rubric rule" for how these are derived)

## Mission statement
<the falsifiable, narrowed statement from Step 1 — not an open-ended study>
```

**`<topic-slug>/SOURCES.md`** — written at the end of Step 2:
```markdown
# Sources: <topic title>

## From second brain (prior captures — treated as saved belief, not fact)
- <thought id / title> — <one line on relevance>

## Freshly researched for this mission
- **Official/primary:** <source name + link> — <one line on what it establishes>
- **Practitioner:** <source name + link> — <one line on what it establishes>

## Disagreements or gaps found
<state plainly if sources conflicted or nothing authoritative turned up — see the sourcing/grounding
contract's fallback rule; leave "None" if not applicable>
```

**`<topic-slug>/RECORD.md`** — written/updated at the end of Step 5, one per mission:
```markdown
# Record: <topic title>

- **Slug:** <topic-slug>
- **Mission:** <one line, copied from MISSION.md>
- **Outcome:** <continue | paused | teach-back passed | exercise verified |
  failure-analysis satisfied | graduated>

## Demonstrated understanding
<what the teach-back actually showed, in the user's own words / paraphrase>

## Exercise + verification evidence
<what was built/run/measured; the observable output named in the applied-exercise contract; actual
result, not just "done">

## Teach-back result
<pass/fail against the rubric written at Step 1/2, restated verbatim here, with the grading applied>

## Failure modes + tests (mandatory failure-analysis gate)
<the specific failure mode(s) explored and what test/check would catch each — this is checked
independently of the teach-back rubric; see "Decision definitions and generic rubric rule">

## Remaining gaps
<anything the rubric didn't cover, or a remediation retry that still missed on the second attempt —
logged here rather than looped on indefinitely>

## Recommended next step
<e.g. "graduate," "continue in a follow-on session," "revisit exercise with a harder case">

## Artifact paths
- Mission: `<topic-slug>/MISSION.md`
- Sources: `<topic-slug>/SOURCES.md`
- Exercise: `<topic-slug>/exercises/...`
```

**`learning_lab/README.md` topic-index entry** — one row appended/updated per topic:
```markdown
| Topic slug | Title | Status | Last updated |
|---|---|---|---|
| rag-reranking-evaluation | RAG reranking evaluation | graduated | 2025-01-15 |
```
`Status` uses the same outcome vocabulary as `RECORD.md`'s Outcome field, collapsed to whichever is most
recent — this file is the equivalent of `CURRENT.md`'s role for `second_brain`, a fast human-scannable
index rather than the durable record itself.

## Sourcing requirement — never second-brain-only

The second brain is a real asset for this skill (personalized context, prior related captures, the
evidence-classification/"informs not dictates" guardrail) — but it is not a substitute for actual
research, and must never be treated as the sole source of truth for a learning mission. Concretely:

- **Step 2 (grounding) always runs both:** a second-brain lookup (`get_context`/`semantic_search`) *and*
  live external research (web search/fetch) — never one or the other. The second brain surfaces what
  you've already encountered; live research surfaces what's actually authoritative right now, including
  material you've never captured.
- **Alpha farming (source curation) is explicitly about identifying real external practitioners**
  (researchers, enterprise architects, maintainers of the relevant Open-Source Software (OSS) project)
  — not generic content
  and not a stand-in for searching your own notes. The second brain isn't a proxy for "who has actually
  solved this."
- **`SOURCES.md` per topic should visibly separate the two:** which sources came from prior second-brain
  captures vs. which were freshly researched for this mission — the same observed-fact-vs-saved-belief
  discipline already designed into evidence classification, applied to sourcing instead of personalization.

## Second-brain capture on graduation

**Decided:** yes — a `Graduate` outcome captures a short thought (via `capture_thought`) pointing at the
`learning_lab/<topic-slug>/` path, not a duplicate of the full record. This makes graduated learning
surface in `get_context`/`semantic_search`/wiki compiles alongside everything else in the brain, while
`learning_lab` remains the durable, detailed record.

**Exact ordering and payload (resolved — previously unspecified):** finalize `RECORD.md` → commit it
locally (per the v0.1 storage protocol above) → **only then** call `capture_thought`, so the pointer
never references a record that doesn't exist yet in `learning_lab`. If the local commit fails for any
reason, skip the capture and tell the user, rather than capturing a pointer to an uncommitted state.

`capture_thought` text template:
```
Graduated: <topic> — <one-line mission>. Demonstrated: <competency level reached>. Outcome: <what the
competency contract confirmed>. Full record: learning_lab/<topic-slug>/RECORD.md
```
No special category is forced — let the second brain's own classification apply naturally, same as any
other capture. If a topic graduates a second time (a follow-on mission under a new slug, per the resume
behavior above), it gets its own new capture — never edits or overwrites a prior graduation thought.

## Open decisions (resolve before or during v0.1 build)

- **Confirm the `learning_lab` project name, GitHub repo URL, and creation timing** — first action when
  work on this actually starts. Not resolved yet; proposed name `learning_lab` as a starting point, its
  own git repo from session one (settled — see "Artifact storage," driven by the mobile-access
  requirement, not just exercises being real code) — but confirm the actual repo URL/org before creating
  anything, and whether the initial local clone lives at `C:\projects\learning_lab\` on this machine or
  wherever else it's cloned first.

## Next step

Build v0.1 (Mode 2 only, 5-step version, with the review fixes applied) as a standalone skill and pilot
it on the RAG reranking mission above. Do not build the router, Mode 1, Mode 3, or the evidence-
classification schema until v0.1 has been used on a real topic and the pilot success criteria have been
checked.

## Glossary — concepts referenced above by keyword only

Terms used throughout this doc as shorthand, expanded here so the plan reads cold without needing the
design conversation that produced it.

**ELI5 / the learning ladder.** Marchese's three-step sequence for explaining any new concept: (1)
"explain it like I'm 5/12/18" — force simplification, with a domain analogy the user already knows
(sports, cooking, whatever fits) as an explicit variant of this step, not a separate technique; (2)
"level-two analysis" — why this specific concept matters to *this* user, tied back to their stated
mission, not an abstract textbook answer; (3) ground it in what the user is already working on,
interviewing for missing context rather than guessing at it. It's the explanation half of Step 2 in this
plan's v0.1 flow, and it's the specific capture (second-brain thought `159e464a`) that motivated building
this system in the first place, rather than just using Claude ad hoc for one-off explanations.

**Alpha farming.** Marchese's term for deliberately seeking out people who are actually doing the thing —
researchers, practicing engineers, maintainers of the relevant tool or library — instead of whichever
content ranks highest or was produced by someone who learned the topic two weeks before making a video
about it. In this plan it shows up as a requirement on Step 2's source-gathering: grounding must include
live external research aimed at real practitioners, not just whatever the second brain already has saved
or whatever a generic search surfaces first.

**Teach-back.** The core verification move: after being taught something, the user explains it back in
their own words, unprompted, before the model offers any commentary. It's what actually distinguishes
"can recognize the right words" from "understands the concept" — a user can nod along to a good
explanation without being able to reproduce or apply it. In this plan it's Step 4's mandatory gate for
Mode 2 and 3, with a defined remediation path (name the gap, re-teach once, retry once, then log as a
Remaining Gap) rather than an infinite loop or a silent pass.

**Mic test.** The specific Marchese technique that teach-back operationalizes (second-brain thought
`b8ec8883`): explain a concept out loud to Claude, and let its follow-up questions reveal blind spots you
didn't know you had. The distinction from teach-back as described above is subtle but real — mic test is
about *discovering* gaps through open-ended follow-up questioning, while this plan's teach-back gate is
about *verifying* specific, pre-written rubric criteria were met. Both rely on the same underlying
mechanism: you don't know what you don't understand until you try to say it out loud.

**Smallest V1.** Marchese's build principle: once a concept is explained, don't keep studying it in the
abstract — build the smallest possible real thing that uses it, immediately. The build itself becomes
the teacher, surfacing gaps that reading or discussion alone wouldn't. This is Step 3 of the v0.1 flow
("applied exercise") and is also why `learning_lab`'s per-topic structure includes an `exercises/`
directory for real, runnable code rather than notes about code.

**Relevance gate.** The admission-time question Marchese's framework asks before any learning starts:
why learn this at all? This plan classifies the answer into three buckets — professionally actionable
(ties to a current or near-term responsibility), capability-building (closes an identified gap, no
immediate deliverable), or intellectually curious (no planned application) — because the three warrant
different depth and different persistence, not a uniform process. It's the first branch in the target
three-mode architecture, though v0.1 doesn't build the full router yet.

**Continuation / scope gate ("topic gravity").** A recurring check, distinct from the one-time relevance
gate above: a mission that was legitimately worth starting can still drift — the recurring failure mode
this plan calls "topic gravity," where a mission to understand RAG quietly grows into implementing
GraphRAG or benchmarking five vector databases nobody asked for. The gate re-asks, at natural
checkpoints: is this still tied to the original mission, or has scope crept past what the mission
actually needs? It's deferred to Mode 3 in the current build sequence (v0.1's single-session Mode 2
cycle is short enough that scope drift is less of a risk, but it becomes necessary once missions span
multiple sessions).

**Zone of Proximal Development (ZPD).** A concept from educational psychology (Vygotsky): the band of
difficulty just above what a learner can already do alone, where they can succeed with guidance and are
stretched without being lost — as opposed to material that's already mastered (no growth) or too far
beyond current ability even with help (frustration, not learning). Matt Pocock's `/teach` skill scopes
each lesson to sit in this band, assessed from the learner's prior state rather than a fixed curriculum.
Deferred to Mode 3/v1.0 in this plan's build sequence, since it depends on the persistent per-topic state
that only the mastery track maintains.

**Evidence classification.** The discipline of tagging every piece of personalized context by what kind
of claim it actually is — observed fact, user-stated preference, saved belief (from the second brain),
external-source claim, agent inference, or the user's current decision — rather than treating all of it
as equally solid "knowledge." The point is that personalization should inform recommendations, but only
the user's present decision should control the learning path; a saved belief from six months ago
shouldn't silently override what the user actually wants today. Declared a *principle* in v0.1 (name it
when citing a saved belief, don't assume it) with the full structured schema deferred to v0.2 — seeing
this fully specified in one v0.1 session isn't required before it's useful in a lighter form.

**Failure-analysis + verification gate.** A requirement this plan adds on top of both source
methodologies, not present natively in either: for any professionally actionable topic, a concept isn't
considered learned until the user can also name its likely failure modes, describe how they'd test for
them, and state how success would be measured — not just explain the concept and build something with
it. This reflects the user's actual job (Software Verification Engineer) and existing annual goals found
in the brain (Software Quality Metrics, Test Suite Automation), and is meant to prevent the common
AI-assisted-learning failure of acquiring enough vocabulary to sound informed without being able to
evaluate or troubleshoot the real thing.
