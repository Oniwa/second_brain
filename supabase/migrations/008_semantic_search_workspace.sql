-- Extend semantic_search to support workspace scoping and return the workspace column,
-- so MCP query tools can default to "current workspace + global" instead of everything.
drop function if exists semantic_search(vector(1536), int, text, text);

create or replace function semantic_search(
  query_embedding   vector(1536),
  match_limit       int     default 10,
  filter_category   text    default null,
  filter_status     text    default 'active',
  filter_workspace  text    default null
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
  workspace    text,
  created_at   timestamptz,
  similarity   float
)
language sql stable as $$
  select
    t.id, t.raw_text, t.title, t.summary, t.category,
    t.people, t.topics, t.action_items, t.urls, t.source, t.workspace, t.created_at,
    1 - (t.embedding <=> query_embedding) as similarity
  from thoughts t
  where
    (filter_category  is null or t.category  = filter_category)
    and (filter_status is null or t.status   = filter_status)
    and (filter_workspace is null or t.workspace = filter_workspace or t.workspace is null)
    and t.embedding is not null
  order by t.embedding <=> query_embedding
  limit match_limit;
$$;
