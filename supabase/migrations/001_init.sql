-- Enable pgvector extension
create extension if not exists vector;

-- Main thoughts table
create table thoughts (
  id          uuid primary key default gen_random_uuid(),
  raw_text    text not null,
  embedding   vector(1536),
  category    text check (category in ('person', 'project', 'idea', 'admin', 'insight')),
  title       text,
  summary     text,
  people      text[] default '{}',
  topics      text[] default '{}',
  action_items text[] default '{}',
  confidence  float,
  source      text,
  status      text default 'active' check (status in ('active', 'needs_review', 'archived')),
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

-- Semantic search index (HNSW for fast approximate nearest-neighbor)
create index thoughts_embedding_hnsw
  on thoughts using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

-- Array filters
create index thoughts_people_gin  on thoughts using gin (people);
create index thoughts_topics_gin  on thoughts using gin (topics);

-- Scalar filters
create index thoughts_category_idx    on thoughts (category);
create index thoughts_status_idx      on thoughts (status);
create index thoughts_created_at_idx  on thoughts (created_at desc);

-- Auto-update updated_at
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger thoughts_updated_at
  before update on thoughts
  for each row execute function set_updated_at();

-- Helper: semantic search (called by MCP server)
create or replace function semantic_search(
  query_embedding vector(1536),
  match_limit     int     default 10,
  filter_category text    default null,
  filter_status   text    default 'active'
)
returns table (
  id          uuid,
  raw_text    text,
  title       text,
  summary     text,
  category    text,
  people      text[],
  topics      text[],
  action_items text[],
  source      text,
  created_at  timestamptz,
  similarity  float
)
language sql stable as $$
  select
    t.id,
    t.raw_text,
    t.title,
    t.summary,
    t.category,
    t.people,
    t.topics,
    t.action_items,
    t.source,
    t.created_at,
    1 - (t.embedding <=> query_embedding) as similarity
  from thoughts t
  where
    (filter_category is null or t.category = filter_category)
    and (filter_status  is null or t.status   = filter_status)
    and t.embedding is not null
  order by t.embedding <=> query_embedding
  limit match_limit;
$$;
