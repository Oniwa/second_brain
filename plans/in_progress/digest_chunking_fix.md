# Fix silent digest truncation (Discord DM chunking)

_Filed 2026-07-26 after the weekly review DM arrived cut off mid-sentence ("You archived a striking number of 'wat…") with no continuation._

## Symptom

The `--review` (and any long `--weekly`) digest arrives in Discord truncated at ~1900 chars, ending mid-word, with no follow-on message. The Gmail copy is unaffected (no length limit there), so content isn't lost — but the channel the user actually reads is silently degraded.

## Root cause

`discord/digest.py` → `send_discord_dm()` (lines 111–136):

1. **Hard char-slice split.** `chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]` cuts at an arbitrary byte offset — mid-word, mid-markdown — instead of on a paragraph/line boundary.
2. **No pacing between chunks.** The loop POSTs each chunk back-to-back. Discord rate-limits consecutive messages to a channel and returns **HTTP 429** on the second message.
3. **429 crashes the send after partial delivery.** `urllib.request.urlopen` raises `HTTPError` on 429. Chunk 1 has already been delivered; the exception unwinds to the caller's `except Exception` (digest.py:195), which prints `✗ Discord DM failed` to the cron log and moves on. Net effect: the user receives only chunk 1, truncated mid-word, and nothing signals that a second chunk was dropped.

## Fix

Rewrite `send_discord_dm()`'s message-sending section. Four parts:

1. **Boundary-aware splitting.** Replace the hard slice with a splitter that packs the message into ≤1900-char chunks breaking on `\n\n` first, then `\n`, then (only if a single line exceeds the limit) whitespace, then a hard cut as last resort. Guarantee: no character is dropped, and reassembling the chunks reproduces the message. Keep markdown intact across the boundary (don't split inside a `**bold**` run when avoidable).
2. **Inter-chunk pacing.** `import time` and add a short `time.sleep()` (~0.5–1s) between chunk POSTs to stay under the per-channel rate limit in the common case.
3. **429 retry.** On `HTTPError` with status 429, read `retry_after` (JSON body `retry_after`, or the `Retry-After` header), sleep that long, and retry the same chunk. Cap retries (e.g. 3) so a persistent failure still surfaces.
4. **Don't fail silently on partial delivery.** If a chunk ultimately fails after retries, raise with context on *which* chunk (index / total) failed, so the cron log shows "delivered 1 of 3" rather than a bare failure — the current behavior hides that earlier chunks already went out.

## Scope notes

- Only the Discord path is affected. `send_gmail()` has no length limit — leave it.
- `--daily` digests are usually short enough to be one chunk, so this has gone unnoticed until the longer `--review` output. The fix covers all three.

## Testing

- Unit-test the splitter: (a) every chunk ≤ 1900 chars; (b) `"".join(chunks) == message`; (c) no chunk starts/ends mid-word when a boundary was available; (d) a single >1900-char line still splits without loss.
- Live test: run `python3 digest.py --review` against a week with a long review and confirm all chunks arrive in order in Discord. Optionally craft a >3800-char synthetic message to force 3 chunks and confirm 429 pacing holds.

## Effort

Small — one function in one file, plus a splitter unit test. High certainty, no schema or infra changes.
