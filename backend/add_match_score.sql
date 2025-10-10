-- Add match_score column to paper_references table
ALTER TABLE paper_references
ADD COLUMN IF NOT EXISTS match_score FLOAT;

-- Add constraint for match_score range
ALTER TABLE paper_references
DROP CONSTRAINT IF EXISTS match_score_valid_range;

ALTER TABLE paper_references
ADD CONSTRAINT match_score_valid_range
CHECK (match_score >= 0 AND match_score <= 100 OR match_score IS NULL);

-- Add index
CREATE INDEX IF NOT EXISTS idx_citations_match_score
ON paper_references (match_score DESC);
