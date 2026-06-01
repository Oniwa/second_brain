# MCP Server Improvements

Improvements surfaced from reviewing Karpathy's LLM wiki approach (Dream Labs AI video).

---

## 1. Knowledge Gap Detection Tool (`get_gaps`)

A dedicated MCP tool that takes stated goals from the brain and recent captures, then asks Claude what's missing — what knowledge, decisions, or actions are implied by the goals but absent from the brain.

Distinct from `get_context` (which retrieves relevant thoughts) — this is inferential: it surfaces what *isn't* there rather than what is.

**Possible interface:**
```
get_gaps(topic?: string) → list of identified gaps relative to goals
```

**Phase:** 5

---

## 2. Skill/Persona Thought Category

A new thought type designed not to surface in semantic search results but to *influence* AI responses. A `skill` thought would contain a distilled perspective from an expert or framework (e.g., "Hormozi business lens", "Karpathy system design principles"). Active skill thoughts would be injected into every `get_context` response.

Requires:
- Schema change: new `type` value (`skill`) in the thoughts table
- MCP update: `get_context` includes all active skill thoughts in its response payload
- New tool or flag on `capture_thought` to mark a thought as a skill

**Phase:** 5

---

## 3. Audit History Surfacing in `get_context`

Review whether `get_context` and `meeting_prep` are leveraging the full capture history (timestamps, source patterns, recency) to produce compounding, personalized context — or just doing point-in-time semantic retrieval.

Karpathy's log.md mechanism works because the AI reads the *history of interactions*, not just stored facts. Check if our equivalent (timestamped thought captures) is being used as effectively as possible in context assembly.

**Phase:** 4–5 (review task, may surface as a quick win)
