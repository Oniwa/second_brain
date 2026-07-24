-- find_by_url — deterministic substring lookup on the urls[] field.
--
-- semantic_search is embedding-only and blind to URL strings, so there was no way to
-- retrieve a thought by its source URL. This RPC closes that gap: the MCP layer
-- canonicalizes the caller's input into a single match key (YouTube → 11-char video ID;
-- everything else → host+path, query/fragment stripped) and passes it here for a
-- server-side, case-insensitive *literal* substring match against each element of urls[].
--
-- strpos (not ILIKE) is deliberate: it treats the key literally, so a video ID or path
-- slug containing `_` or `%` can't accidentally act as a LIKE wildcard.
--
-- Sequential scan is expected and accepted: the existing thoughts_urls_gin index
-- (migration 002) only serves array containment (@>), not substring matching over
-- unnest(urls). At the current table size (~1.9k rows) a seq scan is sub-millisecond;
-- a trigram index is unwarranted. Revisit only if the table grows by orders of magnitude.
--
-- Ordering is deterministic (source, created_at desc, id) so the MCP layer can paginate
-- past PostgREST's 1000-row cap without skipping or duplicating rows — this only ever
-- engages for very broad keys (e.g. a bare domain matching every article from a source).

create or replace function find_by_url(
  match_key     text,
  filter_status text default null,   -- null = all statuses
  match_limit   int  default 1000,
  match_offset  int  default 0
)
returns table (
  id           uuid,
  title        text,
  summary      text,
  category     text,
  people       text[],
  topics       text[],
  action_items text[],
  urls         text[],
  source       text,
  workspace    text,
  status       text,
  is_external  boolean,
  created_at   timestamptz
)
language sql stable as $$
  select
    t.id, t.title, t.summary, t.category,
    t.people, t.topics, t.action_items, t.urls, t.source, t.workspace,
    t.status, t.is_external, t.created_at
  from thoughts t
  where
    (filter_status is null or t.status = filter_status)
    and exists (
      select 1 from unnest(t.urls) as e
      where strpos(lower(e), lower(match_key)) > 0
    )
  order by t.source asc, t.created_at desc, t.id asc
  limit match_limit offset match_offset;
$$;
