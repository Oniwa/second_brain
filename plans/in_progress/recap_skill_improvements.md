# Recap Skill — Codify OB1 Memory Safety Rules

## Context

During a pan session on the Nate B. Jones "OpenClaw, Anthropic, and Gemma 4" article, we captured three OB1 agent memory behavior rules: no transcript dumping, no storing model reasoning traces, and no quietly promoting generated lessons into hidden instructions. These rules prevent the most dangerous memory failure mode — an agent that silently absorbs its own output and starts treating it as ground truth.

When applied to this project, the review identified that `/recap` is the primary write-back mechanism for session memory, and its current rules don't address any of the three OB1 constraints. Specifically: it could silently produce instruction-phrased captures ("always do X") without flagging that these are evidence-grade observations, not standing instructions.

The fix is purely additive — two new rule blocks in the existing skill file. No schema changes, no code changes.

---

## File to Modify

`/home/oniwa/PycharmProjects/second_brain/.claude/commands/recap.md`

---

## Change 1 — Extend "Do NOT capture" section (Step 2)

Add three new bullets to the existing **Do NOT capture** block:

```
- Conversation transcript content verbatim — summarise what was done, don't dump the chat
- Model reasoning traces — the AI's internal deliberation about how to approach a problem has no lasting value
- Anything phrased as a standing instruction for future sessions — that belongs in CLAUDE.md or the memory system, done explicitly, not silently via recap
```

**Why each matters:**
- *Transcript dumping* — inflates the brain with noise that doesn't surface usefully in search
- *Reasoning traces* — captures the process, not the outcome; stale immediately
- *Silent instructions* — the dangerous one: a capture like "always use X pattern" looks like a to-do but acts like a rule if retrieved as context; must be distinguished

---

## Change 2 — Add "Memory grade" rule to Rules section (Step 4)

Add a new rule at the bottom of the existing Rules block:

```
- **Recap captures are evidence, not instructions.** They record what happened and what was decided — not what should always happen. A capture phrased as a rule ("always do X", "never use Y") should be reframed as an observation or decision. If a lesson is important enough to become a standing instruction, update CLAUDE.md or the memory system explicitly in a separate step.
```

---

## Final State of Rules Section

After the change, the Rules section will read:

```
## Rules

- **Be selective.** A typical session should produce 3-8 captures, not 20. Quality over completeness.
- **Open threads are the most important captures.** They're what you'll forget and what causes lost context between sessions.
- **Decisions with reasoning are second most important.** The code shows what you did — the brain captures why.
- **Don't recap the recap.** If you ran `/recap` earlier in the session, don't re-capture what was already captured then.
- **Recap captures are evidence, not instructions.** They record what happened and what was decided — not what should always happen. A capture phrased as a rule ("always do X", "never use Y") should be reframed as an observation or decision. If a lesson is important enough to become a standing instruction, update CLAUDE.md or the memory system explicitly in a separate step.
```

---

## Verification

1. Read the updated skill file and confirm both changes are present
2. Run `/recap` at end of next session — verify no transcript-dump captures, no instruction-phrased captures appear
3. If a recap produces a capture like "always do X", verify it was reframed as "decided to use X for Y reason" before being saved

---

## Note on Scope

The broader OB1 operating rhythm ("recall before work") was also identified as a gap — no retrieve-before-work step exists. That is out of scope here; it would require a separate `/start` or `/context` skill. This plan addresses only the write-back safety rules.
