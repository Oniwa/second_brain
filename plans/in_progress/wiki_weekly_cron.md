# Wire Up Weekly Wiki Compile Cron

**Status:** ready to implement — grill-me pass complete 2026-07-22. All open questions resolved (see Decisions). Not yet built.

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

### Step 2 — Manual one-time full correction (dev machine, watched)
```
python scripts/compile_wiki.py --all
```
Confirm it exits 0, DMs a completion summary (verifies the UA fix), and spot-check a couple of big movers.

### Step 3 — Add the cron job
Add a 6th job to `setup_rpi.py`'s `setup_cron()` list:
```python
wiki = f"{project_path}/scripts/compile_wiki.py"
("Weekly wiki recompile — Sunday 3am", f"0 3 * * 0   {actual_user} {python} {wiki} --all --skip-unchanged >> {log_dir}/wiki-compile.log 2>&1"),
```

### Step 4 — Deploy to the Pi
Re-run `setup_rpi.py` on the Pi (or manually patch `/etc/cron.d/second-brain`) to pick up the new job.

## Files touched

- `scripts/compile_wiki.py` — add `User-Agent` header to `send_discord_dm` (Step 1)
- `scripts/setup_rpi.py` — add job to `setup_cron()` (Step 3)
- No other application-code changes; `compile_wiki.py` is otherwise already cron-ready

## Verify

- Step 1: manual `--all` run DMs a completion summary (no 403 warning in stderr) — proves the UA fix
- `/etc/cron.d/second-brain` on the Pi includes the new wiki job after re-running setup
- Manually trigger the exact cron command once and confirm it exits 0, `wiki-compile.log` shows start/end timestamps and a page count (should be a near-no-op post-correction)
- Let it fire for real on the next Sunday and confirm `wiki_pages.compiled_at` timestamps updated (only for changed pages) without manual intervention, and the completion DM arrives

## Related

- `wiki_implementation.md` — Follow-Up Items #3 (was BLOCKER, now resolved), #2/#11 (Discord DM 403 — closed by Step 1), Order of Operations #12
- `compile_wiki_pagination_bug.md` (done) — its correction is what makes the manual Step 2 a real-cost one-time event
- `CURRENT.md` — "Carried over from May" (cron location) + the deferred full-recompile note
- `roadmap.md` — #1
