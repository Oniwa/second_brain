# Content Fingerprint Deduplication

## What it does
Hashes normalized raw text before insert. If the hash already exists in the DB, the capture is blocked and the existing thought is returned instead. Prevents silent duplicates from accumulating.

---

## Goals & Success Criteria
- Capturing the same text twice from any source (MCP, Discord) results in a blocked capture and a reference to the existing thought
- Updating a thought's `raw_text` to content that already exists in the brain is blocked with a clear message and the existing thought's ID
- All existing thoughts are hashed at migration time, with one copy retained per duplicate group
- `content_hash` is stored on every new thought going forward

---

## Scope
### In Scope
- Deduplication at capture time (all sources)
- Deduplication at `raw_text` update time
- Migration to hash and deduplicate existing 671 thoughts
- Duplicate response handling in MCP server and Discord bot

### Out of Scope
- Near-duplicate / semantic similarity detection (separate future feature)
- Test infrastructure (deferred — no JS test framework selected yet, Python rewrite planned)
- Deduplication on fields other than `raw_text`

---

## Four Files to Change

**1. `supabase/migrations/003_content_hash.sql`** (new file)
- Add `content_hash TEXT` column to thoughts table
- Backfill all existing thoughts — normalize (lowercase, trim, collapse whitespace) then SHA-256
- Skip null `raw_text` entries during backfill
- Deduplicate: keep oldest per group; tiebreaker prefers `active > needs_review > archived`
- Add unique index after backfill and dedup

**2. `supabase/functions/process-thought/index.ts`**
- Add `normalizeText()` — lowercase, trim, collapse whitespace
- Add `hashText()` — SHA-256 via Deno Web Crypto API
- Before embedding + classification: compute hash, query DB for existing match (no status filter), return early with `{ok: false, duplicate: true, id, title, category}` if found
- Add `content_hash` to the insert payload

**3. `mcp/src/server.ts`**
- Add `normalizeText()` and `hashText()` matching the Edge Function exactly
- In `captureThought()`: handle `data.duplicate === true` before existing error check — return `⚠️ Duplicate: already captured as **[title]** [category]\nID: uuid`
- In `updateThought()`: if `raw_text` is being updated, compute new hash, check for existing match against a different thought ID, block with message + existing ID if found, otherwise store new hash with the update

**4. `discord/bot.py`**
- In `handle_capture()`: add a third branch for `result.get("duplicate")` — react ⚠️ and reply with existing thought title and ID

---

## Key Decisions
- **Hash logic location:** Duplicated in Edge Function and MCP server (Option A) — normalization is 3 lines, duplication risk is low
- **Status filter:** None — thoughts of any status (active, needs_review, archived) block new duplicates
- **Backfill tiebreaker:** Keep oldest by `created_at`; prefer active over needs_review over archived on same timestamp
- **Live behavior:** First-come-first-served — existing thought always wins
- **Null handling:** Null `raw_text` skipped in backfill; null captures not permitted
- **Hash parity:** PostgreSQL `sha256()` vs. Deno `crypto.subtle.digest()` — safe for English + URL content

---

## Constraints
- Migration applied via Supabase CLI on a separate machine
- Edge Function must be deployed after migration (column must exist before first live hash check)
- MCP server must be rebuilt and restarted after `server.ts` changes
- Discord bot must be restarted after `bot.py` changes

---

## Edge Cases & Error Conditions
- Archived or needs_review duplicate → blocked, existing thought wins
- Same content, different source → blocked, source field is irrelevant
- `update_thought` sets `raw_text` to existing content → blocked with message + existing ID
- `update_thought` does not change `raw_text` → `content_hash` not touched
- Null `raw_text` in backfill → skipped, `content_hash` left null

---

## Risks
- Hash parity between PostgreSQL and Deno worth a manual spot-check after migration
- Thoughts with null `content_hash` after migration won't be caught by duplicate check — acceptable

---

## Order of Operations
1. Run `003_content_hash.sql` via Supabase CLI
2. Deploy updated Edge Function
3. Build and restart MCP server
4. Restart Discord bot
