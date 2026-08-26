-- ============================================================
-- Rollback: Migration Kategori PJU + Kode Aset Baru
-- Jalankan ini HANYA jika perlu membatalkan migration
-- ============================================================

ALTER TABLE aset_pju DROP FOREIGN KEY fk_aset_kategori;
ALTER TABLE aset_pju DROP INDEX idx_aset_kode;
ALTER TABLE aset_pju DROP INDEX idx_aset_kategori_wilayah_tahun;
ALTER TABLE aset_pju DROP COLUMN id_kategori;
ALTER TABLE aset_pju DROP COLUMN tahun_pemasangan;
ALTER TABLE aset_pju DROP COLUMN kode_aset;
ALTER TABLE aset_pju CHANGE COLUMN kode_aset_legacy kode_aset VARCHAR(50) DEFAULT NULL;
DROP TABLE IF EXISTS kategori_pju;
