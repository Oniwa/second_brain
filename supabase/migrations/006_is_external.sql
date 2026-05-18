ALTER TABLE public.thoughts
  ADD COLUMN IF NOT EXISTS is_external BOOLEAN NOT NULL DEFAULT false;

-- Backfill: pan-captured thoughts always contain 'Source:' in raw_text
UPDATE public.thoughts
  SET is_external = true
  WHERE raw_text ILIKE '%Source:%';
