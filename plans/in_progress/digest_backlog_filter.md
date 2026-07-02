# Digest — Separate Recap "Open Threads" From Ripe To-Dos

Diagnosed: 2026-07-02. **Design not finalized — problem captured, fix is a sketch to be refined later.**

---

## Problem

The daily digest keeps promoting recap-sourced "open threads" into the **Top 3 actions** slot before the user is ready to work on them. The user has been tuning around it ("getting better over time") but it never fully resolves, because the digest has no reliable signal to separate a *ripe personal to-do* from a *deferred project backlog item*.

### Why it happens (root cause)

The digest (`supabase/functions/generate-digest/index.ts`) buckets thoughts on a **single boolean**, `is_external`:

- `is_external = false` → `[PERSONAL]` → **eligible for Top 3 actions**
- `is_external = true`  → `[EXTERNAL]` → themes/patterns only, never a to-do

The external-exclusion design is correct and intentional (see `plans/done/personal_digest_fix.md`) — external pan insights are reference material, not to-dos.

But **recap captures are the user's own work notes**, so they are `is_external = false` and land squarely in `[PERSONAL]`. Two things then make them look like urgent to-dos:

1. `/recap`'s own rules (`.claude/commands/recap.md`) say **"open threads are the most important captures"** and instruct it to phrase them as `"TODO: <next step> — context: …"` (recap.md lines 54, 80). So they read exactly like action items.
2. `/recap` calls `capture_thought` with **no `source`**, so it defaults to `mcp` — making recap open-threads **indistinguishable from a genuine, ripe personal to-do**.

Given a recent, personal, TODO-phrased thought with no distinguishing source, the digest LLM *correctly* elevates it to Top 3. It has zero signal that the user isn't ready to act on it. The current behavior is the model guessing readiness from vibes — which is why it's fuzzy and never fully fixed.

This is the same class of problem the `[EXTERNAL]` split already solved: it works because it's a **deterministic signal**, not a judgment call.

---

## Fix sketch (design TBD — do not implement yet)

Mirror the `[EXTERNAL]` solution: turn "readiness" from an inferred judgment into an explicit signal.

1. **Stamp recap captures with a distinct source.** `/recap` Step 3 sets `source: "recap"` on every `capture_thought` call (one-line change to `recap.md`). Optionally also tag an `open-thread` topic.
2. **Teach the digest a third bucket.** In `formatThoughts`, thoughts with `source: "recap"` (or the chosen marker) render as `[BACKLOG]` alongside `[PERSONAL]`/`[EXTERNAL]`. Update the prompt: `[BACKLOG]` = project backlog / open threads, **not** ripe to-dos — exclude from "Top 3 actions"; surface in a separate line (e.g. `🧵 Open project threads`) or the existing "one thing that's been sitting" slot.

**Result:** three honest buckets — ripe personal actions (Top 3) · project backlog from recaps (separate line, no pressure) · external insights (themes only). The digest stops inferring readiness because the user has told it.

### Open design questions (why this needs more planning)

- **Marker choice:** dedicated `source: "recap"` vs. a first-class `pan_status`-style field vs. a new `category`/`type`. `source` is cheapest but overloads a field meant for provenance; a typed field is cleaner but needs a schema/classifier touch.
- **Promotion path:** how does a backlog open-thread graduate to a ripe Top-3 action when the user *is* ready? Manual re-capture? A flag flip? A digest command? Needs a deliberate, low-friction gesture — not automatic.
- **Retroactive thoughts:** existing recap captures already stamped `source: mcp` won't get the new bucket. Backfill, or accept it only applies going forward?
- **Interaction with the two-gate curation model** (see `pan_skill_improvements.md`): backlog is effectively a third gate — captured, but not yet promoted to "act now."

---

## Related (separate items, cross-referenced)

- **Proactive resurfacing of external/panned insights** — external insights are deliberately kept out of the digest, so nothing ever surfaces them. That's the *opposite* problem (under-surfacing, not over-surfacing) and is tracked as a stub in `open_brain_improvements.md`. Do not conflate with this backlog-filter fix.

## Verification (once implemented)

- A freshly recap'd open-thread does **not** appear in Top 3 actions.
- It **does** appear under the new backlog line.
- Genuine personal to-dos (non-recap, `is_external=false`) still populate Top 3.
- External thoughts still inform themes only.
