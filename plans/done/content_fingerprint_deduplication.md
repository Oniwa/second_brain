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
- Migration to hash and deduplicate existing thoughts
- Duplicate response handling in MCP server and Discord bot

### Out of Scope
- Near-duplicate / semantic similarity detection (separate future feature)
- Test infrastructure (deferred — no JS test framework selected yet, Python rewrite planned)
- Deduplication on fields other than `raw_text`

---

## Four Files to Change

**1. `supabase/migrations/003_content_hash.sql`** (new file)

Steps must execute in this order:
1. Add `content_hash TEXT` column (nullable — null values are valid for thoughts with null raw_text)
2. Audit foreign key references to `thoughts.id` before any DELETE — confirm no dependent tables exist
3. Run dry-run query to list all duplicate groups before deletion (see Dry-Run Query below)
4. Backfill: normalize (lowercase, trim, collapse `/\s+/` → single space) then SHA-256 as hex lowercase
5. Skip null `raw_text` entries — leave `content_hash` null
6. Deduplicate: keep oldest by `created_at`; tiebreaker prefers `active > needs_review > archived` on same timestamp
7. Add **partial** unique index: `CREATE UNIQUE INDEX idx_thoughts_content_hash ON thoughts(content_hash) WHERE content_hash IS NOT NULL`

> ⚠️ Do not add the unique index before dedup — it will fail if duplicates remain.
> ⚠️ Partial index required — a standard unique index on a nullable column still prevents multiple NULLs in some configurations.

**Dry-run query (run before migration to review duplicates):**
```sql
SELECT
  encode(sha256(lower(regexp_replace(trim(raw_text), '\s+', ' ', 'g'))::bytea), 'hex') AS hash,
  count(*) AS copies,
  array_agg(id ORDER BY created_at ASC) AS ids,
  array_agg(title ORDER BY created_at ASC) AS titles,
  array_agg(status ORDER BY created_at ASC) AS statuses
FROM thoughts
WHERE raw_text IS NOT NULL
GROUP BY hash
HAVING count(*) > 1;
```

**2. `supabase/functions/process-thought/index.ts`**

- Add `normalizeText()` — lowercase, trim, collapse whitespace using `/\s+/g` → `' '`
  - Note: JS `\s` matches tabs, newlines, NBSP (U+00A0), and other Unicode whitespace — this is intentional
- Add `hashText()` — SHA-256 via Deno Web Crypto API, output as **hex lowercase string**
  ```ts
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
  ```
- **Move Supabase client creation to the top of the request handler** — before the duplicate check, not after the LLM calls. Otherwise embedding + classification costs are paid on every duplicate.
- Before embedding + classification: compute hash → query DB for existing match (no status filter) → if found, return **HTTP 200** with `{ok: false, duplicate: true, id, title, category}`
  - Must be HTTP 200 (not 4xx) — MCP's `!res.ok` guard must not fire before the duplicate branch is handled
- Add `content_hash` to the insert payload

**Hash parity note:** PostgreSQL backfill uses `encode(sha256(...)::bytea, 'hex')` — also hex lowercase. Both sides must produce identical output. Verify with a spot-check after migration: pick a known thought, hash it in JS, confirm it matches the stored `content_hash`.

**3. `mcp/src/server.ts`**

- Add `normalizeText()` and `hashText()` matching the Edge Function exactly
  - Use Node built-in `crypto`: `require('crypto').createHash('sha256').update(text).digest('hex')` — no new dependency
- In `captureThought()`:
  - Check `data.duplicate === true` **before** the `!res.ok || !data.ok` guard — duplicate response has `ok: false` so the existing guard would throw a cryptic undefined error if checked first
  - Return `⚠️ Duplicate: already captured as **[title]** [category]\nID: uuid`
- In `updateThought()`:
  - If `raw_text` is being updated: compute new hash, query for existing match against a **different** thought ID
  - If match found: block update, return message + existing ID
  - If no match: proceed with update, store new hash
  - **Also rely on the unique index as authoritative guard** — catch unique constraint violations from concurrent updates rather than trusting only the pre-check

**4. `discord/bot.py`**

- In `handle_capture()`: add duplicate branch **after** the `if "error" in result` check (duplicate response has no `error` key, so ordering is safe — but must be explicit)
  ```python
  if result.get("duplicate"):
      await message.add_reaction("⚠️")
      await message.reply(
          f"⚠️ Already in brain: **{result['title']}** [{result['category']}]\nID: `{result['id']}`",
          mention_author=False
      )
      return
  ```

---

## Key Decisions
- **Hash logic location:** Duplicated in Edge Function and MCP server (Option A) — normalization is 3 lines, duplication risk is low
- **Live behavior:** First-come-first-served — existing thought always wins regardless of status
- **Status filter:** None — thoughts of any status (active, needs_review, archived) block new duplicates
- **Backfill tiebreaker:** Keep oldest by `created_at`; prefer active > needs_review > archived on same timestamp
- **Null handling:** Null `raw_text` skipped in backfill; null captures not permitted
- **HTTP status for duplicate:** 200 — ensures client duplicate branch is reached before `!res.ok` guard
- **Unique index:** Partial (`WHERE content_hash IS NOT NULL`) — allows multiple null hashes
- **Race condition on update:** Unique constraint violation is the authoritative guard; pre-check is an optimization only

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
- Concurrent `update_thought` race → unique index constraint violation is caught and surfaced

---

## Risks
- Hash parity between PostgreSQL and Deno — run spot-check query after migration to verify
- Thoughts with null `content_hash` won't be caught by duplicate check — acceptable
- Unexpected duplicates in backfill — run dry-run query first and review before committing migration

---

## Order of Operations
1. Run dry-run query to review duplicate groups
2. Run `003_content_hash.sql` via Supabase CLI
3. Deploy updated Edge Function
4. Build and restart MCP server
5. Restart Discord bot
