# /synth — Meeting Synthesis

Structure raw meeting notes or a transcript into decisions, action items, open questions, and context — then capture each to your second brain.

## Input

The user provides one of:
- Raw meeting notes (pasted directly)
- A meeting transcript (pasted or file path)
- A brief description of what happened (less structured)

Optionally add `--dry-run` to preview captures without writing to the brain.

Optionally add `--meeting "title"` to label the meeting (e.g. `--meeting "1:1 with Mike 4/11"`). If not provided, infer a short title from the content.

---

## Phase 1 — Extract

Read the entire input carefully. Extract every item that falls into one of these categories:

**Decisions** — things that were agreed upon, resolved, or committed to
- Include: what was decided, who decided it, any conditions
- Example: "Decided to defer the dashboard to Q3 — not enough bandwidth this sprint"

**Action items** — specific next steps with an owner
- Include: what needs to be done, who owns it, deadline if mentioned
- Example: "Mike to send updated pricing doc by Friday"
- Example: "Follow up with Sarah about the contract renewal — no deadline set"

**Open questions** — things raised but not resolved
- Include: the question itself, who raised it, any partial answers
- Example: "How do we handle token budget when multiple agents run in parallel? — no answer yet"

**Key context** — important background, facts, or constraints that came up
- Include: anything that would be useful to remember for future meetings or decisions
- Example: "Legal requires all data stored in EU region — affects architecture choices"

**Risks / concerns** — things flagged as potential problems
- Include: the risk, who raised it, any mitigation discussed
- Example: "Mike flagged that the current API rate limits may not hold under production load"

Output each category as a clearly labeled list. If a category has no items, say "None identified."

---

## Phase 2 — Review

Show the full extraction grouped by category. Then show:

```
Meeting: <inferred or provided title>
Decisions:   N
Action items: N  
Open questions: N
Key context: N
Risks: N
Total to capture: N
```

If `--dry-run`: show exactly how each item would be captured (formatted thought text) and stop here with `[DRY RUN — nothing captured]`.

Otherwise ask: **"Capture all N items now?"**

---

## Phase 3 — Capture

For each item, call `capture_thought` with a well-formed thought:

- **Decisions**: prefix with the meeting title — `"[Meeting title] Decision: <what was decided and why>"`
- **Action items**: write as a clear next action — `"Action item from [meeting title]: <what> — Owner: <who> — Due: <when or 'no deadline'>"`
- **Open questions**: write as a question worth tracking — `"Open question from [meeting title]: <the question> — Context: <any partial answer or who raised it>"`
- **Key context**: write as a standalone fact — `"Context from [meeting title]: <the fact or constraint>"`
- **Risks**: write as a flagged concern — `"Risk flagged in [meeting title]: <the risk> — Mitigation discussed: <yes/no + details>"`

Show the `capture_thought` receipt for each item.

After all captures:
```
Synthesis complete.
  Meeting: <title>
  Decisions:    N captured
  Action items: N captured
  Open questions: N captured
  Key context:  N captured
  Risks:        N captured
  Total: N thoughts → second brain
```

---

## Rules

- **One thought per item.** Don't bundle two action items into one capture — they won't surface independently.
- **Write for your future self.** Each capture must make sense without re-reading the notes.
- **Always include the meeting title** in each capture so you can find related items with `get_context "meeting title"`.
- **Decisions and action items are highest priority** — if notes are thin, at minimum get those.
