# URL Capture Fix

## Context
Captured thoughts containing URLs (e.g. YouTube links) preserve the URL in `raw_text` but never extract it into a dedicated field. The LLM drops or buries URLs in `action_items` as plain text, making them unsearchable and invisible in MCP tool output. This fix adds a `urls text[]` column (matching the `people[]`/`topics[]` pattern), extracts URLs via regex in the Edge Function, backfills existing data, and surfaces URLs in all MCP tools and the CLI.

## Files to Change

| File | Action |
|------|--------|
| `supabase/migrations/002_add_urls.sql` | NEW |
| `supabase/functions/process-thought/index.ts` | MODIFY |
| `scripts/backfill_urls.py` | NEW |
| `mcp/src/server.ts` | MODIFY |
| `scripts/brain.py` | MODIFY |

---

## Step 1 — `supabase/migrations/002_add_urls.sql` (NEW)

```sql
-- Add urls column, matching the people/topics pattern
alter table thoughts
  add column urls text[] default '{}';

-- GIN index for array containment queries
create index thoughts_urls_gin on thoughts using gin (urls);

-- Replace semantic_search to include urls in return set
create or replace function semantic_search(
  query_embedding vector(1536),
  match_limit     int     default 10,
  filter_category text    default null,
  filter_status   text    default 'active'
)
returns table (
  id           uuid,
  raw_text     text,
  title        text,
  summary      text,
  category     text,
  people       text[],
  topics       text[],
  action_items text[],
  urls         text[],
  source       text,
  created_at   timestamptz,
  similarity   float
)
language sql stable as $$
  select
    t.id, t.raw_text, t.title, t.summary, t.category,
    t.people, t.topics, t.action_items, t.urls, t.source, t.created_at,
    1 - (t.embedding <=> query_embedding) as similarity
  from thoughts t
  where
    (filter_category is null or t.category = filter_category)
    and (filter_status  is null or t.status   = filter_status)
    and t.embedding is not null
  order by t.embedding <=> query_embedding
  limit match_limit;
$$;
```

Deploy: `supabase db push`

---

## Step 2 — `supabase/functions/process-thought/index.ts` (MODIFY)

**Add URL extraction helper** after the constants block (before the `ClassificationResult` interface):

```typescript
const URL_REGEX = /https?:\/\/[^\s<>"{}|\\^`[\]]+/g;
function extractUrls(text: string): string[] {
  return [...text.matchAll(URL_REGEX)].map(m => m[0]);
}
```

**Extract URLs** alongside the `status` computation (before the insert):

```typescript
const urls = extractUrls(text.trim());
```

**Add `urls` to the insert object** after `action_items`:

```typescript
urls,
```

No changes to `ClassificationResult` or `CLASSIFICATION_PROMPT` — extraction bypasses the LLM entirely.

Deploy: `supabase functions deploy process-thought`

---

## Step 3 — `scripts/backfill_urls.py` (NEW)

Fetches all thoughts where `urls = '{}'`, re-extracts from `raw_text`, patches rows that yield at least one URL. Uses same `load_env` + `urllib` pattern as `brain.py` (no new deps).

Key logic:
- Filter: `?select=id,raw_text&urls=eq.{}&order=created_at.asc`
- Regex: `re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')`
- PATCH: `{"urls": ["https://..."]}` to `/rest/v1/thoughts?id=eq.<ID>`
- `--dry-run` flag prints without writing

Run after migration is deployed:
```bash
python scripts/backfill_urls.py --dry-run   # review first
python scripts/backfill_urls.py             # apply
```

---

## Step 4 — `mcp/src/server.ts` (MODIFY)

**`formatThought()` — add URLs line after `action_items`:**
```typescript
t.urls && (t.urls as string[]).length
  ? `URLs: ${(t.urls as string[]).join(" ")}`
  : "",
```

**`listRecent()` select (line 93)** — add `urls`:
```
"id, title, summary, category, people, topics, action_items, urls, source, created_at"
```

**`getThought()` select (line 294)** — add `urls` to select string and add display line:
```typescript
data.urls?.length ? `**URLs:** ${data.urls.join(" ")}` : "",
```

**`meetingPrep()` select (line 259) and `getContext()` select (line 322)** — add `urls` to both:
```
"id, title, summary, category, people, topics, action_items, urls, source, created_at"
```

`semanticSearch()` uses `supabase.rpc()` — automatically receives `urls` once the SQL function is replaced. No additional change needed.

Rebuild: `cd mcp && npm run build` then restart MCP server.

---

## Step 5 — `scripts/brain.py` (MODIFY)

**`_print_thought()` — add URLs line after `action_items`:**
```python
if t.get("urls"):
    print(f"  URLs:    {' '.join(t['urls'])}")
```

**`recent()` select (line 82)** — add `urls`:
```python
params["select"] = "title,category,summary,people,topics,action_items,urls,source,created_at"
```

`search()` calls the `semantic_search` RPC — no change needed, `formatThought` handles it automatically.

---

## Execution Order

1. Deploy migration (`supabase db push`)
2. Deploy Edge Function (`supabase functions deploy process-thought`)
3. Run backfill (`--dry-run` first, then live)
4. Rebuild + restart MCP server
5. Python CLI changes take effect immediately

---

## Verification

**Edge Function — capture a thought with a URL:**
```bash
curl -X POST "$SUPABASE_URL/functions/v1/process-thought" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"Check this video https://youtu.be/FtCdYhspm7w on agentic design"}'
```
Then query the row: `?id=eq.<ID>&select=urls` — expect `[{"urls":["https://youtu.be/FtCdYhspm7w"]}]`

**Backfill — verify the agentic design thought gets its URL back:**
Check ID `75e71f2f-a74b-41c6-82bf-7e1d67c1430c` has `urls: ["https://youtu.be/FtCdYhspm7w?si=a1hEsCXK8upNW6-k"]`

**MCP — call `get_thought` on a thought with URLs:**
Response should include a `**URLs:**` line.

**CLI:**
```bash
python scripts/brain.py --recent --days 1
```
Thoughts with URLs should show a `URLs:` line. Thoughts without URLs should look identical to before.
