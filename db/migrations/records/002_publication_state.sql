-- records/002_publication_state.sql
-- Adds publication_ready and blocked_claims views for explicit publication state.
-- These views are read-only conveniences — they do not replace the claims table.

-- View: claims ready for publication (all conditions met)
CREATE VIEW IF NOT EXISTS publication_ready_claims AS
SELECT c.*
FROM claims c
WHERE c.status = 'verified'
  AND c.public_citable = 1
  AND c.support_chain_complete = 1
  AND c.stale = 0
  AND NOT EXISTS (
      SELECT 1 FROM publication_blocks pb
      WHERE pb.claim_id = c.claim_id
        AND pb.resolved_at IS NULL
  );

-- View: blocked claims (need resolution before publication)
CREATE VIEW IF NOT EXISTS blocked_claims AS
SELECT c.*,
       pb.reason AS block_reason,
       pb.blocking_since
FROM claims c
LEFT JOIN publication_blocks pb
       ON c.claim_id = pb.claim_id
      AND pb.resolved_at IS NULL
WHERE c.status = 'blocked'
   OR c.public_citable = 0
   OR c.support_chain_complete = 0
   OR pb.block_id IS NOT NULL;
