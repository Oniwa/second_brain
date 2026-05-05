# /recap — Session Auto-capture

Summarize what was accomplished in this Claude Code session and capture the key items to your second brain.

Run this at the end of a work session before closing.

## Step 1 — Gather Session Context

Collect context about what happened this session:

1. Run `git log --oneline -10` to see recent commits
2. Run `git diff HEAD~3..HEAD --stat` to see what files changed
3. Review the conversation history in this session — what was built, decided, or discovered?

---

## Step 2 — Extract What's Worth Capturing

From the session context, identify:

**What was built or shipped**
- Features implemented, bugs fixed, PRs opened/merged
- Include file names and what changed

**Decisions made**
- Architectural choices, approach decisions, things deferred
- Include the reasoning if it came up

**Things learned or discovered**
- Surprising findings, non-obvious behaviors, gotchas
- Patterns that worked well or didn't

**Open threads**
- Things started but not finished
- Follow-ups needed, questions that came up but weren't answered
- Next logical steps

**Do NOT capture:**
- Mechanical steps that are obvious from the code (e.g. "ran npm install")
- Things already captured earlier in the session
- Temporary debugging steps with no lasting value

---

## Step 3 — Capture

For each item worth capturing, call `capture_thought` with a complete, self-contained thought.

Write captures as if briefing your future self coming back to this project after a week away:

- **Built**: `"Implemented X in <file> — does Y. Key design decision: Z."`
- **Decision**: `"Decided to <choice> for <reason>. Alternatives considered: <what was ruled out>."`
- **Learned**: `"Discovered that <finding>. Context: <where/when this matters>."`
- **Open thread**: `"TODO: <what needs doing next> — context: <why it matters, what's blocking it>."`

Show each `capture_thought` receipt as it's captured.

---

## Step 4 — Summary

After all captures:

```
Session recap complete.
  Built/shipped: N captured
  Decisions: N captured  
  Learned: N captured
  Open threads: N captured
  Total: N thoughts → second brain
```

Then suggest the most logical next session starting point based on open threads.

---

## Rules

- **Be selective.** A typical session should produce 3-8 captures, not 20. Quality over completeness.
- **Open threads are the most important captures.** They're what you'll forget and what causes lost context between sessions.
- **Decisions with reasoning are second most important.** The code shows what you did — the brain captures why.
- **Don't recap the recap.** If you ran `/recap` earlier in the session, don't re-capture what was already captured then.
