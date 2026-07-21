# Wire Up Weekly Wiki Compile Cron

**Status:** stub — captured 2026-07-20, needs a short grill-me pass (mainly to confirm the cron-location decision) before implementation. Not yet built.

---

## Context

`compile_wiki.py --all` has been manually run for every recompile since the wiki MVP shipped (`wiki_implementation.md`, Order of Operations #5, #9). Pre-cron hardening is already done — timestamps on run start/end, `--strict`/`--best-effort` exit codes, systemic-error abort (`401/403/529`), 429 retry with backoff, `--skip-unchanged` for cheap incremental runs. The only thing blocking automation is the decision `wiki_implementation.md` flags as a **BLOCKER** in its own follow-up list (#3, "Decide cron location") — everything else needed is already built.

This has been sitting as a blocker since at least 2026-05-09 (last full recompile) — `CURRENT.md` still lists it under "Carried over from May."

## The blocker, re-examined

Original framing: "Pi locks wiki to home network; PC requires machine to be on; on-demand is safest but loses automation."

Worth re-checking before the grill-me session: the Raspberry Pi already runs 5 other scheduled jobs via `/etc/cron.d/second-brain` (`scripts/setup_rpi.py` `setup_cron()`) — daily digest, reminder check, nudge check, weekly digest, weekly review — all of which call Supabase/Anthropic/OpenAI over the internet, not the home LAN. `compile_wiki.py` needs the same three things (Supabase REST access, `ANTHROPIC_API_KEY`, network egress) that `digest.py`/`nudge.py`/`remind.py` already have running successfully on the Pi today. The "locks to home network" framing may have been about SSH/dev-machine access at the time, not actual runtime requirements — worth confirming this is a non-issue rather than treating it as still-open.

## Approach (pending grill-me confirmation)

1. Add a 6th job to `setup_rpi.py`'s `setup_cron()` job list, following the existing pattern:
   ```python
   wiki = f"{project_path}/scripts/compile_wiki.py"
   ("Weekly wiki recompile — Sunday 5am", f"0 5 * * 0   {actual_user} {python} {wiki} --all --skip-unchanged --strict >> {log_dir}/wiki-compile.log 2>&1"),
   ```
   Scheduled before the 7am/8am/9am Sunday jobs so a fresh wiki is available before the weekly digest/review runs (digest could eventually cite wiki pages — not required now, just good ordering).
2. `--skip-unchanged` keeps steady-state runs cheap (only recompiles pages whose thought_count changed since last run).
3. `--strict` so a failed run exits non-zero and is visible in the log / any future monitoring, rather than silently best-effort succeeding.
4. Re-run `setup_rpi.py` on the Pi (or manually patch `/etc/cron.d/second-brain`) to pick up the new job.

## Open questions for grill-me

- **Confirm cron location is actually fine on the Pi** (see re-examination above) — or is there a real constraint (compute, memory, run duration) that makes the Pi unsuitable for a full `--all` pass that the digest/nudge scripts don't hit?
- **Day/time** — Sunday 5am (before the existing Sunday 8am/9am digest jobs) is a starting guess, not decided.
- **Discord completion notification** — should this job also DM a "wiki recompiled: N pages updated" summary like the digest jobs do? Blocked on the separate open "Discord DM 403" bug (`wiki_implementation.md` follow-up #2) if so — may need to land after that fix, or ship without notification initially and log-only.
- **Interaction with `compile_wiki_pagination_bug.md`** — should this cron job wait until the pagination fix ships, so the first automated run compiles against correct counts rather than baking in the known-undercounted numbers? Leaning yes (this is why it's sequenced after the pagination fix, not before, in the roadmap).

## Files touched

- `scripts/setup_rpi.py` — add job to `setup_cron()`
- No application code changes; `compile_wiki.py` itself is already cron-ready

## Verify

- `/etc/cron.d/second-brain` on the Pi includes the new wiki job after re-running setup
- Manually trigger the exact cron command once and confirm it exits 0, `wiki-compile.log` shows start/end timestamps and a page count
- Let it fire for real on the next Sunday and confirm `wiki_pages.compiled_at` timestamps updated without manual intervention

## Related

- `wiki_implementation.md` — Follow-Up Items #3 (BLOCKER), Order of Operations #12
- `compile_wiki_pagination_bug.md` — should land first so automated runs compile correct counts
- `CURRENT.md` — "Carried over from May" section
