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

Collapsed to 5 visible moves (not 10 — see fixes below):
1. Mission + depth (what are you trying to accomplish, what decision/build depends on it, target
   competency — default to "practitioner" and infer from the stated decision rather than asking cold)
2. Smallest knowledge gap + grounded explanation — sourced from **both** the second brain (saved
   beliefs, prior related captures, `get_context`/`semantic_search`) **and** live external research
   (web search/fetch for current authoritative sources — official docs, papers, credible practitioners,
   per Marchese's "alpha farming" principle of seeking real practitioners over generic influencers). The
   second brain is a fast, personalized starting point, not the ceiling — it only contains what's already
   been captured, which is a strict subset of what's authoritative on a given topic, and relying on it
   alone would recursively limit every mission to previously-consumed content.

   Explanation itself follows Marchese's **three-step learning ladder** (the actual capture that
   motivated building this system in the first place — second-brain thought `159e464a`, from the same
   video): (a) **"Explain it like I'm 5/12/18"** — force simplification; a domain analogy the user
   already knows well (sports, cooking, whatever fits) is an explicit variant of this step, not a
   separate add-on; (b) **level-two analysis — why this matters to the user specifically**, not just
   the abstract concept, tied back to the mission from Step 1; (c) **ground it in what the user is
   already working on** — if that context is missing or ambiguous, interview for it rather than
   guessing. All three steps run in sequence before the applied exercise; this replaces an earlier,
   thinner "just add one ELI5 sentence" version of this step.
3. Applied exercise (smallest useful implementation or decision exercise)
4. Teach-back + completion gate (see remediation path below; operationalizes the same idea as the
   "mic test" technique captured from the same Marchese video — thought `b8ec8883` — explain aloud,
   surface gaps from what you can't yet say)
5. Concise learning record + recommended next step (continue / apply / pause / graduate)

**v0.2 — after several real uses.** Improve friction points found in practice; add the evidence
classification schema (see fixes below — deferred here deliberately, not because it's optional forever);
add explicit continue/pause/graduate as a first-class decision; refine the learning-record structure
based on what v0.1 actually needed.

**v0.3 — only after Mode 2 proves useful.** Add Mode 1 (quick explanation) and the routing shell that
dispatches between modes based on the relevance-gate + competency-target answers.

**v1.0 — only when a topic clearly requires sustained mastery.** Add Mode 3: persistent mission
workspace, spaced retrieval, ZPD-scoped lessons, deeper mastery records, scheduled reassessment (the
Pocock mechanisms, now earned rather than assumed).

## Fixes from the Opus 5 review (apply before/while building v0.1)

Two real contradictions, plus simplifications — all reduce scope, none add it:

1. **Evidence classification is a principle in v0.1, not a schema.** It was declared a "hard requirement
   from the first version" while also being deferred to v0.2 in the build sequence — pick one. v0.1
   keeps only the *principle* ("when citing saved second-brain notes, name it as a saved belief and ask
   for confirmation, don't silently assume it"). The full six-field schema
   (`statement`/`classification`/`source`/`captured_at`/`confidence`/`override_allowed`) is v0.2 work.
2. **Completion gate needs a remediation path, not just pass/fail.** On a miss: name the specific gap,
   re-teach only that, retry once; on a second miss, log it as a Remaining Gap and end the session
   anyway (don't loop indefinitely). Add an honest "I just need the answer" exit that ends the session
   without faking a teach-back — for a personal skill, abandonment is the dominant failure mode, not
   shallowness.
3. **Self-grading has no independent check.** Same model teaches and evaluates. Mitigate, don't solve:
   write the rubric *before* teaching and restate it verbatim at grading time; require the user's answer
   in their own words before any model commentary; make "don't complete the user's thinking" a rule about
   one observable behavior (never supply the exercise's answer even if asked twice — offer the plain
   explanation and end instead).
4. **Cut v0.1 to 5 steps, not 10.** Steps 1–4 of the original draft collapse into one exchange;
   "assess current understanding" is inferred from the teach-back, not asked upfront.
5. **Pilot success criteria must be falsifiable, not a 10-item subjective checklist.** See below.
6. **Define state-file location and resume protocol now**, not as an afterthought — cheap to specify
   up front, expensive to retrofit once records exist. **Resolved:** see "Artifact storage" section below
   — a sibling `learning_lab` project, identified by its repo (not a hardcoded path), so it stays
   reachable from any device that can clone/pull it, not just the one where it was first created.
7. **No failure branch specified for stale/conflicting/absent sources** in step 2 — the skill should
   state the disagreement, downgrade the outcome to "needs experiment," and proceed rather than stalling.

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

*Rubric* (written before teaching, restated verbatim at grading time, per fix #3): the teach-back passes
only if the user's own words — not the model's — cover (a) what reranking does differently from initial
retrieval, (b) why it costs something (latency/compute/complexity), and (c) at least one concrete
scenario where skipping it would still be the right call. Partial/vague answers on any one of the three
trigger the remediation path (name the gap, re-teach once, retry once, then log as a Remaining Gap).

**Pilot success criteria (3, not 10):**
1. Did the session end with a defensible yes/no on the reranker?
2. Did it fit one sitting (~60 minutes)?
3. Did the user voluntarily start a second topic within two weeks? (If not, v0.2 should *subtract*
   process, not add it.)

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
mobile Claude Code session that has no access to an arbitrary desktop filesystem path. The skill should
resolve `learning_lab` by **repo identity (its GitHub URL)**, not a hardcoded absolute path — clone it to
whatever local cache location makes sense for the current environment if it isn't already present, work
in it, then commit and push at natural checkpoints (record write, graduation). This sidesteps a known,
already-flagged mistake: `/transcript`'s own doc admits its output path is "hardcoded for the home
Windows PC" and needs multi-machine support — no reason to repeat that here when we can see it coming.
Repo name/path/URL still need to be confirmed before v0.1 (see Open decisions), but the identity model
(repo, not path) is settled. **Scope note:** actually building/testing the mobile flow is explicitly out
of scope for the v0.1 pilot, which stays desktop-only — this only affects how the storage model is
*specified*, so it doesn't need to be rebuilt later.

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
  hardcoded path, per the mobile-access reasoning above.

**Proposed structure (per topic, git-tracked in its own repo, cloned by identity rather than assumed
present at a fixed path):**

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

This also resolves the "state-file location" item from the Opus 5 review fixes above: the identity is
`learning_lab` (a git repo, wherever it's cloned locally), the path within it is `<topic-slug>/`, the
resume rule is "read `MISSION.md` + `RECORD.md` for this topic-slug at the start of any session that
references it, cloning/pulling the repo first if needed," and cross-session continuity doesn't depend on
`second_brain`'s workspace-per-cwd model at all — which is the right call, since a learning mission
(e.g. "RAG") isn't tied to whatever project repo, or even device, you happen to be sitting at that day.

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
