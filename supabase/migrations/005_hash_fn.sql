-- Hash function matching Edge Function normalization:
--   lower(trim(regexp_replace(text, '\s+', ' ', 'g'))) encoded as UTF-8
-- Use convert_to(..., 'UTF8') not text::bytea — bytea cast only works for hex strings.
CREATE OR REPLACE FUNCTION hash_thought_text(raw text)
RETURNS text LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT encode(
    sha256(convert_to(lower(trim(regexp_replace(raw, '\s+', ' ', 'g'))), 'UTF8')),
    'hex'
  );
$$;
