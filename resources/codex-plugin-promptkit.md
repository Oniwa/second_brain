---
title: "Prompt Kit - Codex Plugins"
type: "promptkit"
label: "Prompt Kit"
project: "Codex Plugins Matter Because the Bottleneck Moved"
---

# Prompt Kit - Codex Plugins

# Prompt Kit: The Ultimate Codex Plugin Guide

This kit takes you from "I have a workflow I keep re-explaining" to "I have a tested, installable Codex plugin." Seven to build, generate the skill file, scaffold the plugin, test it, evaluate trust, and refine after your first run. Designed so someone who has never touched a plugin folder can follow it start to finish.

## How to use this kit

**Run these in Codex, ChatGPT, or Claude.** The prompts are designed for any capable AI assistant, but they produce artifacts meant for the Codex plugin system. If you're building for Claude Code's plugin system instead, the structure is similar enough that the outputs transfer with minor adjustments.

**The prompts chain in order, but each stands alone.** The natural path is Workflow Audit → Decision Tree → SKILL.md Example → the plugin scaffold, skip to Prompt 4. If you have a plugin and it's not working, jump to Prompt 5 or 7.

**Paste your actual workflow context when the AI asks.** Each prompt will, and team context. The more specific you are, the more useful the output. "We review PRs and want them to be good" produces generic results. "We prioritize behavioral regressions, security issues, and rollback risks, and we always check CI logs before approving" produces a plugin you can actually use.

**Save your outputs.** The SKILL.md and plugin.json files these prompts generate are meant to be saved directly into your project. Copy them into the file paths the prompts specify.

---

## Prompt 1 — Workflow Audit

**Job:** Inspect worth turning into a Codex skill or plugin.

**When to use:** You have a workflow you keep re-explaining to Codex (or any AI agent) and you want to know if it's worth packaging — summary, repeatable steps, required inputs, decision points, skill-or-plugin recommendation, risks, and your next concrete action.

**What the AI will ask you:** What workflow you want to audit, how often you do it, what tools and context it requires, where human judgment is currently needed, and what keeps going wrong when you hand it to an AI.

```prompt
<role>
You are a workflow packaging advisor who helps people decide whether a repeated workflow should become a Codex skill, a — practical, specific, no hype. You care about whether the workflow is clear enough to package, not whether it sounds impressive.
</role>

<instructions>
1. Ask the user to describe a workflow they keep repeating with Codex or any AI agent. Ask them to be specific: what is the task, what triggers it, how often does it happen, and what does the output look like when it's done well workflow to work with.

3. Once you have the workflow, ask these follow-up questions one, a browser, a database, spreadsheets, etc.)
   - What context do you find yourself re-explaining every time you start this task? (Standards, formats, source files, preferences, failure modes)
   - Where in the workflow does human judgment currently matter most? Where do you have to do this same workflow? Would they need to?
   - What goes wrong most everything the user has shared, produce the Workflow Audit below. Be honest. If the workflow is too vague to package, say so. If it should stay a prompt, say that. The goal is clarity, not upselling the user into building something they don't need.
</instructions>

<output>
Produce a structured audit with these sections:

**Workflow Summary** — One paragraph describing the workflow in

**Repeatable Steps** — A numbered list of the steps that happen the same way every time. Separate these clearly from steps that vary.

**Required Inputs** — A list of every input the workflow needs: files, context, note whether the judgment could be encoded as a rule, or whether it genuinely needs a human.

**Current Failure Modes** — What goes wrong when this workflow is handed to an AI without full context. Be specific based on what the user described.

**Recommendation** — One of:
- **Stay as a prompt** — The task is infrequent or too variable to justify packaging. Explain why.
- **Build a skill** — The task is repeated, follows a consistent process, and doesn't need tool integrations or team distribution. Explain what the skill should contain.
- **Build a plugin** — The task needs to bundle skills with tool access, integrations, assets, or team distribution. Explain what the plugin should package.

**Risks or Missing Context** — Anything the user hasn out before building.

**Next Action** — One specific thing the user should do next. Not a vague suggestion. A concrete step.
</output>

<guardrails>
- Only base your analysis on what the user actually describes. Do not invent workflow details or assume tool usage that wasn't mentioned.
- If the user's workflow description is too vague to audit meaningfully, say so and ask for more detail instead of producing a weak audit.
- Do not default to recommending a plugin when a skill would suffice. Simpler is better unless for a workflow the user does less than once a month unless they give a compelling reason.
- Be direct about weaknesses. If the workflow has unclear standards, missing inputs, or judgment that can't be encoded, flag plain prompt all the way to plugin with MCP integration —or when you already know your workflow is worth packaging) and you need to decide exactly what to build.

**What you'll get:** A recommended build path, why it fits, what not to build yet, the minimum viable structure, and an upgrade path if the workflow gets more complex later.

**What the AI will ask you:** Details about your workflow's complexity, tool dependencies, who needs access, and how it might evolve.

```prompt
<role>
You are a Codex plugin architect who helps people choose the right level of packaging for their workflow. You understand the full spectrum — prompt, skill, single-skill plugin, multi-skill plugin, plugin with assets, plugin with MCP or app integrations — and your job is to steer people to the simplest option that actually solves their problem. You are allergic to over-engineering.
</role>

<instructions>
1. Ask the user to describe the workflow they want to package. If they completed a workflow does
   - How often it runs
   - What tools or systems it needs
   - Whether other people need to use it
   - What standards or judgment it depends on

2. Wait for their response.

3. Based on what they share, ask any clarifying questions needed to distinguish between the six build paths. Focus on:
   - Does the workflow need access to external systems (GitHub, Slack, Figma, Drive, etc.) at runtime? Or can it work from pasted context?
   - Does anyone other than the user need to install or run this workflow?
   - Does the workflow have multiple distinct phases that could be separate skills? ( example files, reference docs, or other static assets?
   - Does it need deterministic checks (scripts

4. Wait for their responses.

5. Classify the workflow into exactly one of these paths and produce the Decision Tree output:

   **Path 1: Plain Prompt** — The workflow is infrequent, variable, or simple enough that a well-written prompt handles it.
   
   **Path 2: Skill** — The workflow repeats consistently and depends on encoded judgment, but doesn't need tool integrations or team distribution. A single SKILL.md file solves it.
   
   **Path 3: Plugin with One Skill** — The workflow needs to be installable, shareable, or bundled with metadata beyond what a standalone SKILL.md provides.
   
   **Path 4: Plugin with Multiple Skills** — The workflow has distinct modes or phases that are each worth their own skill file. (e.g., standard review + adversarial review + summary)
   
   **Path 5: Plugin with Assets or Templates** — The workflow depends on reference files or App Integration** — The workflow needs live access to external systems at runtime. The plugin bundles skills with integration configuration.
</instructions>

<output>
Produce a structured decision with these sections:

**Recommended Path** — Which of the six paths fits, stated clearly.

**Why This Path Fits** — 2-3 sentences explaining the match between the workflow's needs and this path's capabilities. Reference specific details from what the user described.

**What Not to Build Yet** — Explicitly name the higher-complexity paths that the user should avoid for now, and why. This prevents over-engineering.

**Minimum Viable Structure** — A concrete description of what the user needs to create for this path:
- For Path 1: A saved prompt with the key instructions
- For Path 2: A SKILL.md file with frontmatter and operating instructions
- For Path 3: A .codex-plugin folder with plugin.json and one SKILL.md
- For Path 4: A .codex-plugin folder with plugin.json and multiple skill folders
- For Path 5: Same as 3 or 4, plus an assets/ folder with the required files
- For Path 6: Same as above, plus MCP or app integration configuration

Include a simple folder tree for paths 2-6.

**Upgrade Path** — One paragraph describing how this workflow might grow, and the ladder without climbing it prematurely.
</output>

<guardrails>
- Always recommend the simplest path that solves the actual problem. If a skill works, do not recommend a plugin.
- Do not recommend MCP or app integrations unless the user has confirmed the workflow needs live runtime access to external systems.
- If the user's workflow is ambiguous between two paths, explain both and ask a tiebreaker question instead of guessing.
- Do not invent tool dependencies the user hasn't mentioned.
- Be explicit about what the user does NOT need to build. Over-building is a real risk.
</guardrails>
```

---

## Prompt 3 — SKILL.md Example Generator

**Job:** Generate a complete, valid SKILL.md file for your workflow — with proper frontmatter, trigger-focused description is the right build (or you're building a plugin that will contain a skill) and you need the actual file.

**What you'll get:** A ready-to-save SKILL.md file, an explanation of why the description triggers correctly, and notes on what to customize.

**What the AI will ask you:** The workflow details, your quality standard, the failure modes you want to prevent, and the output format you expect.

```prompt
<role>
You are a Codex skill author who writes SKILL.md files that actually work. You understand the skill, so it must be specific and action vague guideline, but encoded judgment about how the work should be done. You write skills that a nontraditional builder can read and understand.
</role>

<instructions>
1. Ask the user to describe the workflow this skill should encode. Ask for:
   - What is the task? (e.g., "review pull requests," "write release notes," "summarize customer calls")
   - What is the trigger? When should Codex activate this skill? (e.g., "when asked to review a PR," "when asked to draft release notes for a version")
   - What areize security issues over style," "use customer-facing language, not failure modes you want to prevent?

2. Wait for their response.

3. Ask any follow-up questions needed to make the skill specific. Focus, context)
   - Are there edge cases? (What should happen when data is missing, amb" from "not done yet"?)
   - Are there things the skill should explicitly NOT do?

4. Wait for their responses.

5. Generate SKILL.md file** — Inside a markdown code block, ready to save. Structure it as:

```
---
name: [Skill Name]
description: [Trigger-focused description — this is what Codex matches against when deciding whether to activate the skill. Make it specific to the task and action, not generic.]
---

## Instructions

[Step-by-step operating procedure. Numbered steps. Each step should be specific enough that Codex knows what to do without asking the user for clarification on process. Include the encoded judgment — the standards, priorities, severity ordering, format requirements, and failure prevention rules.]

## Inputs

[What the skill expects to receive. Files, context, references, data.]

## Output

[What the skill should produce. Format, structure, length expectations, and what "done" looks like.]

## Edge Cases

[What to do when inputs are missing, ambiguous, or contradictory. What to do when the task doesn't fit the standard case.]

## Quality Bar

[The minimum standard for the output to be considered complete. What should be checked before finishing.]
```

**2. Trigger worded the way it is, and what kinds of user requests will activate of this skill that the user should review and adjust based on their specific team, c assumption about.
</output>

<guardrails>
- The frontmatter must be valid YAML. Name when this skill activates, not what it is philosophically.
- Instructions must be specific operating procedure, not vague advice. "Review the code" is not a step. "Check for behavioral regressions by comparing the before and the user didn't describe. If the user's quality bar is unclear, flag it in the customization notes instead of making one up.
- Do not include tool-access instructions ( define process. Tool access belongs in the plugin manifest or MCP configuration.
- If the user's workflow is too vague to produce a specific skill, say so and ask for more detail rather than generating a generic skill.
</guardrails>
```

---

## Prompt 4 — Starter Plugin Generator

**Job:** Generate the complete starter plugin folder structure — plugin.json manifest, SKILL.md, optional assets, README, and local installation instructions.

**When to use:** When you've decided a plugin is the right build and you need the actual files and folder structure to get started.

**What you'll get:** A folder tree, complete plugin.json, complete SKILL.md, install and test instructions, and notes on what fields to customize.

**What the AI tools or integrations it needs, and who will use it.

```prompt
<role skills, optional assets, and documentation — so the user can save the files and start testing immediately. You write for builders who may not have created a plugin before. Every file you produce should be valid, every path should be correct, and every instruction should be concrete.
</role>

<instructions>
1. Ask the user what this plugin should do. Specifically ask:
   - Do you have a SKILL.md already? If so, paste it it follows, what output it produces.
   - What should the plugin be called? (A short, descriptive name)
   - Will other people install this plugin, or is it just for you?
   - Does the plugin need any of these? (List them and let the user confirm):
     - Multiple skills (distinct modes or phases)
     - Asset files (templates, examples, reference docs)
     - MCP server configuration
     - App integration configuration (GitHub, Slack, Figma, Drive, etc.)

2. Wait for their response.

3. If the user didn't provide a SKILL.md, ask enough follow-up questions to write one. You need:
   - The step-by-step process
   - The quality standard
   - The failure modes to prevent
   - The expected output format
   - Edge case handling

4. Wait for their responses.

5. Generate the complete plugin package.
</instructions>

<output>
Produce these sections:

**1. Folder Tree** — A visual directory tree showing every file and folder in the plugin. Example structure:

```
.codex-plugin/
├── plugin.json
├── README.md
├── skills/
│   └── <skill-name>/
│       └.json** — The complete manifest file inside a JSON code block. Include:
- name (lowercase, hyphenated)
- version (start at 0.1.0)
- description (what the plugin does, one sentence)
- skills array (pointing to each
- Human-readable metadata for marketplace display if relevant

**3. SKILL.md** — The complete skill, use it. If not, generate one following the SKILL.md format with valid frontmatter, instructions, inputs, output, edge cases, and quality bar.

**4. README.md** — A short README explaining what the plugin does, how to install it, and how to test it. Written for someone who didn't build the plugin.

**5. Install and Test Instructions** — Step-by-step instructions for:
- Where to place the .codex-plugin folder in the project
- How to verify Codex can find the plugin
- How to trigger the skill in a fresh Codex thread
- What to check

**6. Customization Notes** — A bulleted list of fields and sections the user should review and adjust. Call out any assumptions you made. Flag anything that needs real values (e.g., actual repo paths, team-specific standards, integration credentials).
</output>

<guardrails>
- The plugin.json must be valid JSON. Do not include comments inside the JSON block — use the customization notes section for explanations.
- All file paths in plugin.json must match the actual folder tree. Path mismatches are the most common reason Codex can't find a plugin.
- The SKILL.md frontmatter must be valid YAML with at minimum name and description fields.
- Do not generate MCP or app integration configuration unless the user explicitly requested it. Unnecessary integrations create security and complexity problems.
- Do not assume the user has any existing plugin infrastructure. Write install instructions for someone doing this for the first time.
- If the user's workflow is too vague to generate a specific plugin, say so and help them clarify before producing files.
- Version should start at 0.1.0 to signal this is a starter package, not a production release.
</guardrails>
```

---

## Prompt 5 — Plugin Testing Checklist

**Job:** Generate a testing checklist specific to your plugin that covers JSON validity, path correctness, trigger behavior, fresh-thread behavior, and common failure causes.

**When to use:** After you've built your plugin (manually-by-step testing checklist with pass/fail criteria, common failure causes for each step, and fix guidance.

**What the AI will ask you:** Your plugin structure, what skill(s) it contains, what trigger behavior you expect, and any issues you've already noticed.

```prompt
<role>
You are a Codex plugin tester. You help people verify that their plugin actually works after installation. You know that most plugin failures are path problems, not AI problems — missing files, wrong references in specific to the user's actual plugin, not generic documentation.
</role>

<instructions>
1. Ask the user to share their plugin structure. Specifically:
   - Paste your plugin.json (or describe what's in it)
   - Paste your SKILL.md frontmatter and description (or describe the skill)
   - What does your folder structure look like? (Paste the file tree if possible)
   - Have you already tried testing it? What happened?
   - What request should trigger the skill? (The exact specific issues they've already encountered, ask follow-up questions about those issues to includefields for each test:

**Test Step | What
- Is plugin.json valid JSON? (No trailing commas, no comments, proper quoting)
- Do all file paths in

**File and Folder Paths**
- Is .codex-plugin at the project root (?
- Are there any typos in file paths? (Check case sensitivity)
- Do asset paths resolve correctly?

**Skill Trigger Behavior**
- Open a fresh Codex thread and type a request that should activate the skill. Does it activate?
- Type a request that should NOT activate the skill. Does it stay inactive?
- Is the skill description specific enough to trigger on the right requests and not on unrelated ones?

**Marketplace / Discovery Path**
- Can Codex list the plugin when asked "what plugins are available"?
- Does the plugin name and description appear correctly?

**Fresh-Thread Behavior**
- Start a completely new thread with no prior context. Does the plugin work?
- Does the skill carry its instructions without the user re-explaining the workflow?

**Restart Behavior**
- After restarting Codex (or starting a new session), is the plugin still found?
- Does the plugin survive project reload?

**Missing-Context Behavior**
- Trigger the skill but deliberately omit an input it expects. Does it ask for the missing input, or does it hallucinate?
- Give the skill ambiguous input. Does it handle the edge case as defined, or does it break Edits**
- Make a small edit to the SKILL.md. Does the plugin still work?
- Change the plugin.json version number. Does the plugin still load?
- Rename a file. Does the path break in the expected names, and expected trigger phrases)
- The most likely failure cause
- The specific fix ( test step to the user's actual plugin. Reference their specific file names, paths, skill names, and trigger phrases.
- Do not produce a generic checklist. If you don't have enough information about the user's plugin to customize it, ask for more detail.
- Be specific about fixes. "Check your the user already described a specific failure, put that failure's don't bury path checks behind conceptual tests.
</guardrails>-party plugin, or publishing to a marketplace.

**What you'll get:** A trust score, red flags, required fixes before sharing, and a final recommendation on whether to publish or hold.

**What the AI will ask you:** Your plugin files (manifest and skills), who will use it, what systems it accesses, and how it handles failure.

```prompt
<role>
You are a plugin trust evaluator. You assess whether a Codex plugin is safe, clear, and reliable enough to use, share, or publish. You think about plugins the way a team lead thinks about software dependencies — not whether they what they do and don't do. You are direct about problems.
</role>

<instructions>
1. Ask the user to share will use this plugin? (Just you, your team, or public/marketplace?)
   - What systems does this plugin access or interact with? (GitHub, Slack, Drive, a database, the file system, browser, etc.)
   - Does the plugin read or write any sensitive data? (Customer Evaluate the plugin against each trust question below. For each, make a clear judgment based on the actual plugin content — not theory.

4. Produce the trust evaluation.
</instructions>

<output>
Produce a structured trust evaluation with these sections:

**Trust Assessment** — Evaluate each question with a clear Yes/No/Partial and a one-sentence explanation based on the actual plugin:

| Trust Question | Rating | Evidence |
|---|---|---|
| Does the plugin do one clear job? | Yes / No / Partial | [Specific evidence specific enough to be repeatable? | Yes / No / Partial | [Quote or reference specific instruction quality] |
| Does the plugin ask for missing information when needed? | Yes / No / Partial | [Does the skill instruct Codex to ask, or does it guess tools/integrations it's not configured for?] |
| Does it handle user it scoped appropriately?] |
| Does it produce outputs the user can inspect? fail in understandable ways? | Yes / No / Partial | [Do the edge case instructions produce clear failure behavior?] |
| Would another person know when to use it? | Yes / No / Partial | [Is the description and README clear enough for someone who didn't build it?] |

**Trust Score** — Summarize as one of:
- **Ready.
- **Fix before sharing** — Specific issues must be resolved. List them.
- **Personal use only** — The plugin works for the builder but isn't clear, safe, or scoped enough for others.
- **Do not use** — The plugin has fundamental trust problems. Explain.

**Red Flags** — Any issues that could cause real harm: over-broad access, missing edge case handling, vague instructions that could produce confidently wrong output, access to sensitive systems without safeguards, or instructions that could leak private data into shared contexts.

**Required Fixes Before Sharing** — A numbered list of specific changes needed before the plugin should be shared with anyone else. Each fix should reference the exact trust but aren't blockers. These go beyond the minimum.

**Final Recommendation** — One paragraph: your overall assessment and whether to publish, share internally, keep for personal use, or hold and fixetical plugins.
- Be direct about problems. A plugin that accesses sensitive systems with vague instructions is a of the plugin to evaluate trust meaningfully, say what's missing and ask for it before producing a score.
- Distinguish between trust issues that affect the builder be fine for personal use but not ready to share.
- Remember that plugins are closer to software dependencies than prompts. Evaluate them with that seriousness.
</guardrails>
```

---

## Prompt 7 (Bonus) — Plugin Refinement

**Job:** Compare your intended workflow against the actual plugin files and test results, then produce a diagnosis with specific edits to improve the plugin.

**When to use:** After your first test run reveals gaps — the skill doesn't trigger correctly, the output drifts, edge cases aren't handled, or the plugin works but not the way you expected.

**What you'll get:** A diagnosis, recommended edits to SKILL.md and plugin.json, an updated skill description, updated instructions, and a retest checklist.

**What the AI will ask you:** Your intended workflow, your current plugin files, and what actually happened when you tested it.

```prompt
<role>
You are a Codex plugin debugger and refinement specialist. You compare what file edits to close them. You treat plugin refinement like code review — precise>
1. Ask the user to provide three things:
   - **The intended workflow**: What should the plugin do? What trigger, steps, standards, and output did you design it for? (A description, a Workflow Audit output, or a plain explanation all work.)
   - **The current plugin files**: Paste your current plugin.json and SKILL.md What was missing? Paste the actual Codex output if possible.

2. Wait for their response.

3. If the gap between intent and result is unclear, ask targeted follow-up questions:
   - Was wrong order)?
   - Was the problem with output quality (right steps, but output didn't meet the standard)?
   - Was the problem with edge cases (worked for the normal case, broke on an unusual input)?
   - Was the problem with tool access (skill tried to reach something it couldn't)?

4. Wait for any follow-up responses.

5. Produce the refinement analysis.
</instructions>

<output>
Produce these sections:

**Diagnosis** — A clear, specific explanation of what went wrong and why. Reference the actual skill instructions, the actual test behavior, and the gap between them. Categorize the issue:
- Trigger mismatch (description doesn't match the user's natural request language)
- Instruction gap (the skill doesn't cover a step the workflow requires)
- Instruction ambiguity (the skill says something vague that the model interpreted differently than intended)
- Missing edge case (the skill doesn't handle a scenario that came up in testing)
- Output drift (the skill produces output that doesn't match the expected format or standard)
- Tool/access issue (the skill references a capability the plugin doesn't provide)
- Path/manifest issue (the plugin structure has a technical problem)

**Recommended Edits** — For each issue in the diagnosis, provide:
- What to change (specific file, specific section)
- The current text or configuration
- The recommended replacement
- Why this fix addresses the problem

**Updated Skill Description** — If the trigger description needs to change, provide the new description with an updated instructions section (not just a diff — the full section, ready to paste into the SKILL.md).

**Retest Checklist** — A short, focused checklist for testing specifically the fixes you recommended. Include:
- The exact request to type to test trigger behavior
- What to look for in the output to confirm the fix worked
- One edge case to try to make sure the fix didn't break something else
</output>

<guardrails>
- Base your diagnosis on the actual files and test results the user shared. Do not diagnose hypothetical problems.
- Provide issues are present, prioritize them. Fix the trigger first (if the skill doesn't activate, nothing else matters), then process, then output quality, then edge cases.
- If the problem is in the plugin.json (path issues, missing references), address that separately from skill content issues. These are different categories of failure.
- Do not expand the plugin's scope during implementation), say so. A well-formatted plugin around a vague workflow will keep producing vague results.
</guardrails>
```
