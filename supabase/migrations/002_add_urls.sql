-- Add urls column, matching the people/topics pattern
alter table thoughts
  add column urls text[] default '{}';

-- GIN index for array containment queries
create index thoughts_urls_gin on thoughts using gin (urls);

-- Drop and recreate semantic_search to change return type (add urls column)
drop function if exists semantic_search(vector(1536), int, text, text);

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
