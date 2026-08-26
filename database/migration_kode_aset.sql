-- ============================================================
-- Migration: Kategori PJU + Kode Aset Baru
-- Format baru: PJUP-UH2-26-001
-- v2: Disesuaikan struktur aktual (PK=id_aset, kode_aset_legacy sudah ada)
-- ============================================================

-- 1. Tabel kategori_pju (master, dikelola admin)
-- ============================================================
CREATE TABLE IF NOT EXISTS kategori_pju (
  id           INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  kode         VARCHAR(6)   NOT NULL UNIQUE COMMENT 'Misal: PJUP, PJUL, PJUK, PJUM',
  nama         VARCHAR(100) NOT NULL        COMMENT 'Nama lengkap kategori',
  deskripsi    VARCHAR(255) DEFAULT NULL,
  aktif        TINYINT(1)   NOT NULL DEFAULT 1,
  urutan       INT          NOT NULL DEFAULT 0 COMMENT 'Urutan tampil di dropdown',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed data kategori default
INSERT IGNORE INTO kategori_pju (kode, nama, deskripsi, urutan) VALUES
  ('PJUP', 'PJU Jalan Protokol/Kota',    'PJU di jalan kota/protokol sesuai Perwal 50/2022', 1),
  ('PJUL', 'PJU Jalan Lingkungan',        'PJU di jalan lingkungan perumahan',                 2),
  ('PJUK', 'PJU Lingkungan Kampung',      'PJU di gang/jalan kampung',                         3),
  ('PJUM', 'PJU Makam',                   'PJU di area pemakaman',                             4),
  ('PJUW', 'PJU Wisata',                  'PJU di kawasan wisata dan ruang publik',            5),
  ('PJUS', 'PJU Sekolah/Fasilitas Umum', 'PJU di area sekolah dan fasum lainnya',             6);

-- ============================================================
-- 2. Update tabel aset_pju
-- Struktur aktual: PK = id_aset, kode_aset_legacy sudah ada
-- ============================================================

-- Tambah kolom id_kategori (FK ke kategori_pju), AFTER id_aset
ALTER TABLE aset_pju
  ADD COLUMN id_kategori INT UNSIGNED DEFAULT NULL
    COMMENT 'FK ke kategori_pju'
    AFTER id_aset;

-- Tambah kolom kode_aset baru (format baru), AFTER id_kategori
-- (kode_aset_legacy sudah ada di tabel, tidak perlu RENAME)
ALTER TABLE aset_pju
  ADD COLUMN kode_aset VARCHAR(20) DEFAULT NULL UNIQUE
    COMMENT 'Format baru: PJUP-UH2-26-001'
    AFTER id_kategori;

-- Tambah kolom tahun_pemasangan, AFTER kode_aset
ALTER TABLE aset_pju
  ADD COLUMN tahun_pemasangan YEAR DEFAULT NULL
    COMMENT 'Tahun pemasangan aset, dipakai untuk generate kode'
    AFTER kode_aset;

-- Foreign key kategori (tipe harus match: INT UNSIGNED)
ALTER TABLE aset_pju
  ADD CONSTRAINT fk_aset_kategori
    FOREIGN KEY (id_kategori) REFERENCES kategori_pju(id)
    ON UPDATE CASCADE ON DELETE SET NULL;

-- Index untuk pencarian kode (prefix matching saat auto-suggest)
CREATE INDEX idx_aset_kode ON aset_pju(kode_aset);
CREATE INDEX idx_aset_kategori_wilayah_tahun
  ON aset_pju(id_kategori, id_wilayah, tahun_pemasangan);

-- ============================================================
-- 3. View helper: suggest index berikutnya
-- ============================================================
-- Dipakai backend untuk endpoint GET /api/aset/suggest-kode
-- Contoh query:
--   SELECT COALESCE(MAX(
--     CAST(SUBSTRING_INDEX(kode_aset, '-', -1) AS UNSIGNED)
--   ), 0) + 1 AS next_index
--   FROM aset_pju
--   WHERE kode_aset LIKE 'PJUP-UH2-26-%';

-- ============================================================
-- 4. Verifikasi
-- ============================================================
SELECT 'kategori_pju' AS tabel, COUNT(*) AS jumlah FROM kategori_pju
UNION ALL
SELECT 'kolom kode_aset baru',
  COUNT(*) FROM information_schema.columns
  WHERE table_name='aset_pju' AND column_name='kode_aset'
  AND table_schema=DATABASE();
