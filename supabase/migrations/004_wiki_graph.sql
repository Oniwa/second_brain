-- Wiki pages table: compiled synthesis of thoughts per topic/person
-- thought_edges is deferred to 006_thought_edges.sql (Phase 2)

CREATE TABLE IF NOT EXISTS public.wiki_pages (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  slug             TEXT        NOT NULL UNIQUE,
  title            TEXT        NOT NULL,
  content          TEXT        NOT NULL,
  entity_type      TEXT        NOT NULL CHECK (entity_type IN ('topic', 'person', 'project', 'auto')),
  entity_name      TEXT        NOT NULL,
  thought_count    INT         NOT NULL DEFAULT 0,
  stale            BOOLEAN     NOT NULL DEFAULT false,
  last_compiled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX wiki_pages_entity_type_idx ON public.wiki_pages (entity_type);
CREATE INDEX wiki_pages_entity_name_idx ON public.wiki_pages (entity_name);
CREATE INDEX wiki_pages_stale_idx       ON public.wiki_pages (stale) WHERE stale = true;

-- Reuse set_updated_at() defined in 001_init.sql
CREATE TRIGGER wiki_pages_updated_at
  BEFORE UPDATE ON public.wiki_pages
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
