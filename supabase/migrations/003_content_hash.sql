-- Dry-run before applying — review duplicate groups first:
--
-- SELECT
--   encode(sha256(convert_to(lower(regexp_replace(trim(raw_text), '\s+', ' ', 'g')), 'UTF8')), 'hex') AS hash,
--   count(*) AS copies,
--   array_agg(id ORDER BY created_at ASC) AS ids,
--   array_agg(title ORDER BY created_at ASC) AS titles,
--   array_agg(status ORDER BY created_at ASC) AS statuses
-- FROM thoughts
-- WHERE raw_text IS NOT NULL
-- GROUP BY hash
-- HAVING count(*) > 1;

-- Step 1: Add column (nullable — null raw_text thoughts are valid)
ALTER TABLE thoughts ADD COLUMN content_hash TEXT;

-- Step 2: Backfill existing thoughts
UPDATE thoughts
SET content_hash = encode(
  sha256(convert_to(lower(regexp_replace(trim(raw_text), '\s+', ' ', 'g')), 'UTF8')),
  'hex'
)
WHERE raw_text IS NOT NULL;

-- Step 3: Remove duplicates — keep oldest per hash; tiebreaker: active > needs_review > archived
DELETE FROM thoughts
WHERE id IN (
  SELECT id FROM (
    SELECT id,
      ROW_NUMBER() OVER (
        PARTITION BY content_hash
        ORDER BY
          created_at ASC,
          CASE status WHEN 'active' THEN 0 WHEN 'needs_review' THEN 1 WHEN 'archived' THEN 2 ELSE 3 END ASC
      ) AS rn
    FROM thoughts
    WHERE content_hash IS NOT NULL
  ) ranked
  WHERE rn > 1
);

-- Step 4: Partial unique index — allows multiple NULL hashes (thoughts with null raw_text)
CREATE UNIQUE INDEX idx_thoughts_content_hash ON thoughts(content_hash) WHERE content_hash IS NOT NULL;
