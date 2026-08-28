-- =============================================================================
-- Rollback: wilayah_sektor + mutasi_aset
-- =============================================================================
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS mutasi_aset;
ALTER TABLE wilayah DROP COLUMN IF EXISTS sektor;

SET FOREIGN_KEY_CHECKS = 1;
SELECT 'Rollback wilayah_mutasi selesai.' AS status;
