# Cross-Tool, Cross-Machine Skill Sync — Plan Stub

**Status:** stub — captured 2026-07-03, **needs a real planning/scoping session before implementation**. Several open questions below are blocking; don't build from this sketch alone. Continue this file (add answers to Open Questions, revise the design, then move to a real implementation plan) next time this is picked up.

---

## Context / motivation

Started from a narrow question ("can we symlink the global grill-me to this repo's copy") and grew into a real cross-environment problem once the actual usage pattern came out:

- The user works across **two machines**: Linux at home (Claude Code), Windows at work (GitHub Copilot CLI — corporate-approved tool)
- They want their second-brain skills (**`grill-me`**, **`recap`** confirmed so far) usable from **both tools**, kept in sync from **one source-controlled location** (this repo), not hand-copied and left to drift
- `recap` in particular depends on the `second-brain` MCP server being reachable from whichever tool is running it — confirmed already registered globally for Claude Code (`~/.claude.json` top-level `mcpServers`, not project-scoped); Copilot CLI equivalent not yet set up or tested

## What's confirmed so far

1. **Sync mechanism: copy-based, not symlinks.** Windows symlinks need Developer Mode or admin rights (not guaranteed); a script that copies repo → global location works identically on both OSes with no special privileges. Decided over symlinks-with-fallback. Trade-off accepted: one-way (repo → global), needs a trigger (manual re-run, or a git hook later) rather than being live-shared.
2. **Copilot CLI skill format is the same markdown structure as Claude Code** — same frontmatter, same body. The user has directly copied Claude Code skill `.md` files into Copilot CLI and had them work as-is. This contradicts my initial web research (which found custom-slash-commands-from-markdown listed as an open GitHub `copilot-cli` feature request, with `.github/agents/*.agent.md` custom agents as the documented mechanism) — **the user's direct hands-on experience is the source of truth here, not that research; the web-search findings should be treated as possibly stale/incomplete, not authoritative.**
3. **Copilot CLI skills live under `.copilot/skills/<name>/`** (per user) — a directory per skill, not a flat `<name>.md` file like Claude's `.claude/commands/<name>.md`.
4. Copilot CLI does support MCP servers, configured at `~/.copilot/mcp-config.json` (per web research — not yet verified firsthand by the user, since they don't have Copilot CLI on this machine to check).
5. This machine (home/Linux) does **not** have Copilot CLI installed at all — it only exists on the work PC. So nothing about the Copilot side can be verified or tested from here; everything Copilot-related needs confirming against the actual work-PC setup (ideally by the user pasting a real example, or checking next time they're on that machine).

## Open questions — blocking, needs the user's input from the work PC

- **Exact file name inside `.copilot/skills/<name>/`** — is it always the same name as the skill directory (e.g. `.copilot/skills/grill-me/grill-me.md`), a fixed convention like `SKILL.md`, or something else? Not yet confirmed.
- **Scope of `.copilot/skills/`** — is this directory resolved relative to the **current repo** (like `.claude/commands/` is project-relative), or is there a **user-level** equivalent (like `~/.claude/commands/`) that applies across all repos without copying per-repo? This matters a lot: if it's repo-relative only, then "usable in every work repo" needs either (a) copying the skill into every work repo's `.copilot/skills/`, or (b) some global/env-var mechanism (the web research mentioned `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` for a different, instructions-file feature — unclear if it also applies to `.copilot/skills/`). Needs checking against Copilot CLI's actual docs/behavior or the user's own working setup.
- **MCP registration on Copilot CLI** — needs verifying `~/.copilot/mcp-config.json` is the right file, its schema, and whether the same `node mcp/dist/server.js` entry point works from a Windows machine (path separators, whether `node` is on PATH there, whether the repo/build even needs to live on the work machine at all or could point elsewhere).
- **Does the whole second_brain repo need to be cloned onto the work machine**, or just the `mcp/dist/server.js` build output + the two skill files? Bringing this personal repo (which contains `credentials.json`, `token.json` at the root) onto a corporate machine is worth a deliberate decision, not an assumed default — flag this explicitly in the real planning session rather than skipping past it.
- **Reconcile canonical source layout** — now that content is confirmed identical between tools, does each skill need one shared source file copied to two destinations (`~/.claude/commands/<name>.md` and `.copilot/skills/<name>/<file>.md`), or should the repo maintain them as genuinely separate per-tool copies in case they diverge later (e.g. if Copilot's tool-calling conventions ever need different phrasing)? Leaning toward single shared source + copy to both destinations, but not decided.
- **Git-hook automation** — worth wiring a `post-merge`/`post-checkout` hook (via `core.hooksPath` pointing at a repo-tracked `.githooks/` dir) so pulling this repo auto-refreshes the global copies, instead of relying on remembering to re-run a script? Mentioned as a possible follow-up, not committed to.

## Current on-disk state (as of 2026-07-03, home/Linux machine)

- `second_brain/.claude/commands/{recap,grill-me}.md` — committed, canonical source (commits `8acb77a`, `723bef3`)
- `~/.claude/commands/recap.md` and `~/.claude/commands/grill-me.md` — currently **symlinks** to the repo copies (leftover from the initial symlink-based approach, before the copy-based decision above). Old backups sit alongside as `*.bak.<timestamp>` files, not deleted.
- `meal_planner/.claude/commands/grill-me.md` — also currently a **symlink** to this repo's copy, same leftover state, `.bak` alongside.
- The old global `~/.claude/commands/pan.md` (stale, predated the 7/1 dedup-hardening work) was backed up and removed — `pan`/`synth`/`transcript` confirmed repo-local only (user only ever runs `/pan` from within this repo).
- `scripts/link_global_skills.py` — the original **symlink-based** script, still present/committed as-is. **Needs to be rewritten as copy-based** (and likely renamed) once the Copilot side is scoped — not yet done, since the design changed mid-session and Copilot specifics are still unresolved. Don't treat this file as current/correct — it reflects the superseded symlink approach.
- No Copilot CLI config of any kind exists yet, anywhere (confirmed empty `~/.copilot/` on this machine; work-machine state unknown/unverified).

## Suggested next steps when resuming this

1. On the work PC, look at one real `.copilot/skills/<name>/` example the user has already built — get the exact file name and confirm the frontmatter is truly identical to Claude's.
2. Confirm whether `.copilot/skills/` is repo-scoped or user-global on that machine.
3. Decide the credentials/repo-on-work-machine question explicitly.
4. Only then rewrite `scripts/link_global_skills.py` (or a replacement) as a single copy-based sync script covering both tools' destinations, decide on the git-hook question, and reconcile the leftover symlinks on this machine and in `meal_planner` to match whatever the final mechanism is.
