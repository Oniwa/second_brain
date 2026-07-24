# Wiki-First Routing + Automemory Bridge

Two independent fixes surfaced by comparing the second-brain architecture against Nate Herk's "Every Level of a Claude Second Brain" video (panned 7/20, `DTCyvo6cC54`). Not yet grilled or implemented.

---

## 1. Wiki-first routing in `get_context`

**Gap:** `getContext()` in `mcp/src/server.ts:517` goes straight to semantic search + keyword match on raw `thoughts`. It never touches `wiki_pages`, even though a compiled wiki page for that exact topic may already exist. `get_wiki_page`/`list_wiki_pages` are separate tools the agent has to remember to call — there's no automatic fallback hierarchy (specific source → wiki → raw thoughts) like the video describes.

**Approach — two-tier response, not a hard gate:**
- **Tier 1 (wiki match):** query `wiki_pages` with a bidirectional `ILIKE` on `entity_name` vs. the topic string, across all `entity_type`s, ordered by `thought_count DESC`, limit ~3. If any match, prepend it — title, slug, stale flag, and a one-line excerpt (not the full page body, to avoid bloating output) — with a pointer to call `get_wiki_page` for the complete synthesis.
- **Tier 2 (raw thoughts):** keep the existing semantic + keyword merge, but if a wiki match was found in Tier 1, filter to thoughts created after that page's `last_compiled_at` — presented as "newer, not yet in wiki" — otherwise show the full unfiltered list as today.
- Exact/substring matching (not embedding similarity) since `wiki_pages` has no embedding column — adding one is out of scope for this change.

**Files touched:** `mcp/src/server.ts` only (`getContext` function + its tool description). No schema or migration changes.

**Out of scope (flag, don't build now):** applying the same fallback to `meeting_prep` — same pattern, but a separate change if wanted later.

**Verify:** rebuild MCP server (`npm run build` in `mcp/`), then call `get_context` once on a topic with a compiled wiki page (check `compiled-wiki/topics/` for a name) and once on a topic without one — confirm wiki-first behavior in the first case and unchanged behavior in the second.

---

## 2. Automemory → second-brain bridge

**Gap:** Claude Code's native `/memory` (files in `~/.claude/projects/-home-oniwa-PycharmProjects-second-brain/memory/*.md`) and the second-brain `thoughts` table are fully disconnected. Feedback/project memories saved via auto-memory are invisible to `semantic_search`, `get_context`, digests, and the wiki.

**Direction — one-way, automemory → thoughts.** Not the reverse. The second-brain is the deep store; `MEMORY.md` should stay a lightweight session index, not balloon with everything already in the brain.

**Design decision (2026-07-24) — platform-agnostic / multi-source.** The user runs **both Claude Code (Linux home) and GitHub Copilot CLI (Windows work PC)**, each with its own agent memory store. Build the bridge **source-agnostic from the start** so a second tool is "add a directory + an adapter," not a rewrite:
- The script scans a **list** of memory sources, each defined by `{ path, source_tag, adapter }` — e.g. `automemory-claude`, `automemory-copilot`.
- A per-source **parser adapter** normalizes that tool's memory format into the common shape (name, description, body, type). Claude Code's is per-file YAML frontmatter; Copilot's format is **unconfirmed** (see coupling below).
- Dedup state is keyed by **`(source_tag, name)`**, not `name` alone, so the two stores never collide.
- **Implement the Claude Code arm now** (fully unblocked on this machine). **Defer the Copilot arm** — it's coupled to roadmap #10 (`cross_tool_skill_sync.md`) on three unknowns that can only be resolved from the work PC: (a) the two memory stores live on **different machines**, so the sync must run where each memory lives and each machine must reach Supabase (work-PC reachability is #10's open question); (b) Copilot CLI's memory **file format/location** is unconfirmed (same `.copilot/` layout question as #10); (c) the `/recap` trigger is per-tool — Copilot's recap must exist on Windows to fire its sync, which depends on #10's cross-tool recap sync landing.

**Approach — new sync script, `scripts/sync_automemory.py`:**
1. For each configured memory source, read every `*.md` file in its directory except the index file (`MEMORY.md` for the Claude source), and run it through that source's adapter.
2. Adapter parses the memory format into the common shape — for Claude Code: YAML frontmatter (`name`, `description`, `metadata.type`).
3. Compute a SHA-256 fingerprint of the body; keep a small local state file (gitignored, e.g. `.automemory_sync_state.json`) mapping `(source_tag, name) → last-synced fingerprint` so unchanged memories are skipped on repeat runs.
4. For new/changed memories, call the existing `process-thought` pipeline (same path `brain.py` capture uses) with:
   - `raw_text` = frontmatter description + body
   - `source = "<source_tag>"` (e.g. `automemory-claude`, `automemory-copilot`)
   - a fixed `topics` tag `automemory` added post-classification so these stay filterable/excludable across all sources
   - category mapping: `project→project`, `feedback→insight`, `reference→admin`, `user→insight`

**Trigger:** piggyback on the existing `/recap` skill (already runs at end-of-session and already writes to the brain) rather than adding a new cron job — call the sync script as a step in `/recap` so it's automatic on a cadence already in use. Each tool's own recap syncs its own local memory source (the Copilot arm rides #10's cross-tool recap sync).

**Files touched:** new `scripts/sync_automemory.py` (with the source-config table), new gitignored state file, small addition to `.claude/commands/recap.md` to invoke it. (Copilot adapter + its recap hook land later, with #10.)

**Verify:** run the script once manually against the current memory dir, confirm exactly one thought appears via `list_recent`, tagged `automemory`; run it again immediately and confirm zero new captures (fingerprint dedup working).

---

## Deferred (considered, not adding)

- **Context vs. connections separation** — already effectively handled by the pan skill's Evaluate phase filtering what gets captured; no passive/live feed exists that would need it.
- **Always-on/autonomous layer (Gbrain/Hermes-style)** — existing digest/nudge/reminder cron jobs already deliver proactive surfacing at much lower cost than a persistent agent process; no concrete friction yet to justify it.

## Source

- Video: youtube.com/watch?v=DTCyvo6cC54 — Nate Herk, "Every Level of a Claude Second Brain Explained"
- 16 thoughts captured 7/20/2026 under this source, retrievable via `get_context("Nate Herk Claude Second Brain Explained")`
