# Wire Up Weekly Wiki Compile Cron

**Status:** Step 1 shipped (UA fix), Step 4 shipped (cron job added to `setup_rpi.py`). The manual full correction (originally Step 2, renumbered to Step 3) attempted 2026-07-22 and failed — see Update below. A new Step 2 (smoke test) was added as a result, to run before retrying the full correction. Step 5 (Pi deploy) not started. **Step 6 (git-publish the compiled mirror) added 2026-07-24 — not started, and must be grilled before implementing (see the ⚠️ note on Step 6). Without it the cron regenerates pages only on the Pi's local disk and the `Oniwa/compiled_wiki` GitHub mirror silently goes stale.**

## Update — 2026-07-22: first `--all` attempt failed, root causes fixed, not yet re-run

Two unrelated bugs surfaced during the first real `--all` run, both now fixed:

1. **`OUTPUT_DIR` pointed at the wrong folder.** The constant was `compiled-wiki` (hyphen) — a folder that doesn't exist. The actual git-tracked wiki (remote `Oniwa/compiled_wiki`, 154 existing pages) lives at `compiled_wiki` (underscore). Fixed — `compile_wiki.py` now writes to the correct folder. Supabase (the real source of truth for `wiki_pages`) was never affected by this bug; only the local markdown mirror would have landed in the wrong place.
2. **Sonnet 4.6 → 5 upgrade broke response parsing.** Sonnet 5 defaults to adaptive thinking **on** when `thinking` is omitted (4.6 defaulted to off), so `content[0]` became a `thinking` block instead of `text` on many calls — 19 of 418 pages made real, billed API calls (~$4) that then threw `KeyError: 'text'` and produced nothing. Fixed by explicitly setting `thinking: {"type": "disabled"}` and parsing by scanning for the `text`-type block instead of assuming index 0 (`compile_wiki.py` and both edge functions).
3. Separately, ~397/418 pages failed on an unrelated local DNS blip (`getaddrinfo failed`) during the same run — not billed, not a code bug, likely just a network drop.

**Net result of the attempt: 1/418 pages compiled successfully** ("documentation"). The correction run has not yet completed.

**Before re-running:**
- `wiki_thinking_ab_test.md` (new stub) — whether to enable adaptive thinking for wiki synthesis specifically is an open, deliberately deferred question; disabled is the current safe default across all 3 Sonnet call sites, not a tested decision.
- Confirm `compiled_wiki` resolves the same way on the Linux machine — it needs to exist as a sibling directory to `scripts/` (i.e., the private wiki repo cloned into the `second_brain` checkout at `compiled_wiki/`), same as this Windows machine. Not yet verified on Linux.
- **New Step 2 (smoke test)** — run the 3-entity smoke test below *before* retrying the full `--all` correction, to catch any other lurking Sonnet-5-migration bugs cheaply instead of finding out mid-run again.

---

## Context

`compile_wiki.py --all` has been manually run for every recompile since the wiki MVP shipped (`wiki_implementation.md`, Order of Operations #5, #9). Pre-cron hardening is already done — timestamps on run start/end, `--strict`/best-effort exit codes, systemic-error abort (`401/403/529`), 429 retry with backoff, `--skip-unchanged` for cheap incremental runs. The only thing that was blocking automation was the "decide cron location" decision — now resolved.

## Decisions (grill-me, 2026-07-22)

1. **Location: the Pi.** `digest.py`/`nudge.py`/`remind.py` already run there against Supabase/Anthropic/OpenAI over the internet; `compile_wiki.py` needs the identical three things (Supabase REST, `ANTHROPIC_API_KEY`, egress). The old "locks to home network" framing was about SSH/dev access, not runtime — a non-issue. The only thing a full `--all` stresses that the digest scripts don't is ~417 sequential Sonnet calls in one run; a 3am slot removes any run-duration concern.

2. **Schedule: Sunday 3am, weekly — `0 3 * * 0`.** Weekly matches the existing digest/review rhythm; the wiki is a synthesis layer, not a live feed, so daily churn buys little. 3am lands hours before the Sunday 8am digest / 9am review (so a fresh wiki is available first) and gives a long run the whole night.

3. **Cron command: `--all --skip-unchanged`, no `--strict`.**
   - `--all --skip-unchanged` **is** "only recompile what changed" — `--all` walks every qualifying page; `--skip-unchanged` skips any whose stored `thought_count` already matches the current count (compile_wiki.py:806/828/850). In steady state this touches only the handful of pages whose counts moved that week.
   - **Dropped `--strict`** (the plan's earlier draft hardcoded it). `--best-effort` is a deprecated no-op — the only real toggle is `--strict`, and it *only* affects the completed-with-per-page-errors case. The failures worth alerting on — credit exhaustion / auth / overload (`401/403/529`) — **already** abort early and exit 1 regardless of `--strict` (`notify_and_exit(exit_code=1)`). So the clean binary is **exit 1 = systemic abort, exit 0 = ran to completion**; the Discord DM / log reports any per-page errors with detail (`_build_dm`). `--strict` would only add false alarms (one flaky page flips a 416/417-success run to "failed"). Nothing consumes the exit code today anyway (no `MAILTO`, no monitor).

4. **Sequencing: run the one-time full correction manually first, *then* enable the cron.**
   - The pagination fix (2026-07-21) changed nearly every page's count and ~287 pages don't exist yet (417 qualify now vs ~130 before). So the *first* `--all` run is a full ~417-page Sonnet spend no matter what — `--skip-unchanged` can't shortcut it, because those pages' content is genuinely stale against corrected data. This is a one-time event, not a recurring cost.
   - **Do it by hand on the dev machine/PC**, watched, with **plain `--all`** (no `--skip-unchanged`, no `--strict`) to force a full recompile of all 417 qualifying pages. Spot-check a couple of big movers (e.g. "AI agents" 108→330) to confirm the corrected wiki looks right. Running off-Pi keeps the Pi free and makes it easy to cancel if something looks wrong.
   - **Then** enable the Pi cron. Because the DB now holds correct counts, the first automated Sunday run is already cheap (`--skip-unchanged` skips everything unchanged). This matches how `CURRENT.md`/`roadmap.md` already frame the full recompile — a deliberate, real-cost, explicit action, not run ad hoc.
   - **Amended 2026-07-22:** after the first attempt burned ~$4 on 19 pages before a code bug was caught, a smoke test (Step 2) was added ahead of the full correction — 3 single-entity real calls to catch parsing/response bugs cheaply before committing to all 418 pages again.

5. **Fold in the Discord-DM 403 fix (one line).** The completion DM is already built into `compile_wiki.py` (`notify_and_exit` → `send_discord_dm`) but returns 403 (`wiki_implementation.md` follow-up #2/#11). Root cause found during grill-me: `compile_wiki.py`'s `send_discord_dm` (lines 393–408) sends no `User-Agent` header, so urllib defaults to `Python-urllib/3.x`, which Discord 403s. `digest.py:106` sets `User-Agent: "DiscordBot (https://github.com/Oniwa/second_brain, 1.0)"` and its DM works. Add the same header to `compile_wiki.py` → the Sunday cron DMs "🧠 Wiki compile complete — N page(s)" instead of silently 403-ing into the log. Closes `wiki_implementation.md` #2/#11.

## Known limitations (accepted)

- **`--skip-unchanged` uses `thought_count` as the change signal.** A thought *edited* without changing a page's count won't trigger recompile of that page. Acceptable for a weekly synthesis layer; it's the existing behavior.
- **Log rotation: out of scope.** All 6 jobs append with `>> log 2>&1` and none rotate; a weekly `--skip-unchanged` run logs very little. If it ever matters, a single `logrotate` drop-in covers all second-brain logs at once — not special-cased here.

## Approach

### Step 1 — One-line UA fix (before anything else)
In `compile_wiki.py`'s `send_discord_dm`, add the `User-Agent` header to both requests, mirroring `digest.py:106`:
```python
headers={
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (https://github.com/Oniwa/second_brain, 1.0)",
}
```

### Step 2 — Smoke test (new, 2026-07-22 — added after the failed first attempt)
Before spending on all 418 pages again, run one entity of each type through the real (non-dry-run, non-`--all`) path, to catch any other Sonnet-5-migration bugs beyond the two already found — 3 calls instead of 418:
```
python scripts/compile_wiki.py --topic "AI agents"       # largest topic in the corpus (330 thoughts) — stresses big-input synthesis, most footnotes/citations
python scripts/compile_wiki.py --person "Tammy"           # exercises compile_single_person (separate code path from topics)
python scripts/compile_wiki.py --project "Second Brain"   # exercises compile_single_project (separate code path again)
```
This is deliberately not `--dry-run` — dry-run doesn't call the model at all, so it can't catch a parsing/response bug like the one that just happened. `--topic`/`--person`/`--project` are the cheap real-call path: 3 entities instead of 418.

For each, verify:
- Exits without a Python traceback or `✗` error
- Writes to `compiled_wiki/<topics|people|projects>/<slug>.md` (confirms the `OUTPUT_DIR` fix — not the old, wrong `compiled-wiki` hyphen folder)
- The Supabase `wiki_pages` row updates (`thought_count`, `last_compiled_at`)
- The actual content is structurally sane on read-through — correct section headers, footnote citations resolve to real sources, no leftover raw JSON or thinking-block artifacts leaking into the markdown

If all three pass, proceed to Step 3. If any fails, that's a third bug to find and fix before spending on the full run.

### Step 3 — Manual one-time full correction (dev machine, watched)
```
python scripts/compile_wiki.py --all
```
Confirm it exits 0, DMs a completion summary (verifies the UA fix), and spot-check a couple of big movers.

### Step 4 — Add the cron job
Add a 6th job to `setup_rpi.py`'s `setup_cron()` list:
```python
wiki = f"{project_path}/scripts/compile_wiki.py"
("Weekly wiki recompile — Sunday 3am", f"0 3 * * 0   {actual_user} {python} {wiki} --all --skip-unchanged >> {log_dir}/wiki-compile.log 2>&1"),
```

### Step 5 — Deploy to the Pi
Re-run `setup_rpi.py` on the Pi (or manually patch `/etc/cron.d/second-brain`) to pick up the new job.

**Prerequisite for Step 6 — confirm the wiki repo exists on the Pi (added 2026-07-24).** The compiled markdown lives in a **separate git repo** at `compiled_wiki/` (remote `https://github.com/Oniwa/compiled_wiki.git`, its own `.git`, gitignored by the parent — *not* a submodule, so a `second_brain` clone does **not** bring it along). Before the git-publish step can work on the Pi, verify:
- `compiled_wiki/` is cloned as a sibling of `scripts/` inside the Pi's `second_brain` checkout (same layout as dev). If missing, `git clone https://github.com/Oniwa/compiled_wiki.git compiled_wiki` there. (This is the same "confirm `compiled_wiki` resolves on Linux" check the 2026-07-22 update already flagged for the compile step — Step 6 makes it a hard requirement, not just a nicety.)
- Its remote/branch are correct (`git -C compiled_wiki remote -v`, `git -C compiled_wiki branch`).
- **Non-interactive push auth is configured** (see Step 6 — this is the real blocker, cron has no TTY).

### Step 6 — Commit & push the compiled_wiki mirror (git-publish)

> ⚠️ **GRILL BEFORE IMPLEMENTING.** Do not build Step 6 until it has been through a `/grill-me` pass. Two things need resolving first: (a) where the git logic lives (`--git-publish` flag vs. cron shell chain vs. wrapper) and (b) the non-interactive push-auth mechanism (PAT vs. SSH deploy key). The shape below is a **proposed** starting point for that grill, not an approved spec. Same rule applies to the workspace-hybrid scoping follow-up in the project-pages plan — design first, then build.

The cron regenerates markdown into `compiled_wiki/` but nothing publishes it — `compile_wiki.py` has zero git logic today. Add a publish step so the weekly run's output reaches GitHub.

**Where the logic lives (leaning, confirm in a short grill):** a `--git-publish` flag on `compile_wiki.py` rather than chaining shell in the cron line — the script already knows the compiled/skipped counts and exit status, so it can build a meaningful commit message and only publish on a clean (exit-0) run. After a successful `--all`, when `--git-publish` is set:
1. **Only if something changed** — guard on `git -C compiled_wiki status --porcelain`; if empty, skip (no empty commits on weeks where `--skip-unchanged` touched nothing).
2. `git -C compiled_wiki add -A`
3. `git -C compiled_wiki commit -m "Weekly wiki recompile {DATE} — {N} page(s) updated"` (mirror the Discord DM's counts).
4. `git -C compiled_wiki push`
5. **Report push success/failure in the completion Discord DM** (extend `_build_dm`), so an auth/network failure surfaces instead of dying silently in the log. A push failure should not crash the run — the DB is already updated; the mirror just lags a week.

The Sunday cron command (Step 4) then becomes `... --all --skip-unchanged --git-publish >> …`.

**Open sub-decision — non-interactive auth (the real blocker):** cron has no TTY, so `git push` must authenticate without prompting. Two options, decide before deploy:
- **HTTPS + stored PAT** — a fine-scoped (`repo` on `compiled_wiki` only) personal access token in the Pi's git credential store (`git config credential.helper store`), or a `.netrc`. Simple; token needs periodic rotation.
- **SSH deploy key** — a per-Pi deploy key with write access added to the `compiled_wiki` repo, remote switched to `git@github.com:...`. No expiry, revocable per-device; slightly more setup.

Lean SSH deploy key (no rotation, device-scoped), but this is a genuine choice — grill briefly. Whichever is chosen, it's a one-time Pi setup folded into Step 5.

## Files touched

- `scripts/compile_wiki.py` — add `User-Agent` header to `send_discord_dm` (Step 1); fix `OUTPUT_DIR`, disable thinking, robust text-block parsing (found during the failed Step 3 attempt, before this plan had a Step 2 smoke test); **add `--git-publish` (commit+push `compiled_wiki`, only-if-changed, report in DM) — Step 6**
- `scripts/setup_rpi.py` — add job to `setup_cron()` (Step 4); **cron command gains `--git-publish`; Pi setup must ensure `compiled_wiki` is cloned + push auth configured — Steps 5/6**
- `supabase/functions/process-thought/index.ts`, `supabase/functions/generate-digest/index.ts` — same thinking/parsing fix (found same day, same root cause)

## Verify

- Step 1: manual `--all` run DMs a completion summary (no 403 warning in stderr) — proves the UA fix
- Step 2: all 3 smoke-test entities compile cleanly and land in the correct folder — proves no further Sonnet-5-migration bugs before the real spend
- `/etc/cron.d/second-brain` on the Pi includes the new wiki job after re-running setup
- Manually trigger the exact cron command once and confirm it exits 0, `wiki-compile.log` shows start/end timestamps and a page count (should be a near-no-op post-correction)
- Let it fire for real on the next Sunday and confirm `wiki_pages.compiled_at` timestamps updated (only for changed pages) without manual intervention, and the completion DM arrives
- Step 6: after a run that changed ≥1 page, confirm a new commit landed on `Oniwa/compiled_wiki` on GitHub (not just the Pi's local disk) and the completion DM reports the push; after a no-op `--skip-unchanged` week, confirm **no** empty commit was created

## Related

- `wiki_implementation.md` — Follow-Up Items #3 (was BLOCKER, now resolved), #2/#11 (Discord DM 403 — closed by Step 1), Order of Operations #12
- `compile_wiki_pagination_bug.md` (done) — its correction is what makes the manual Step 3 a real-cost one-time event
- `CURRENT.md` — "Carried over from May" (cron location) + the deferred full-recompile note
- `roadmap.md` — #1
