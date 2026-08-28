-- =============================================================================
-- Migration: wilayah_sektor + mutasi_aset
-- Tanggal : 2026-08-28
-- Deskripsi:
--   1. Tambah kolom `sektor` ke tabel `wilayah`
--   2. Buat tabel `mutasi_aset` untuk log mutasi & stok opname
--   3. Seed data sektor 14 kemantren Kota Yogyakarta
-- Jalankan: mysql -u USER -p DBNAME < migration_wilayah_mutasi.sql
-- Rollback : database/rollback_wilayah_mutasi.sql
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. Tambah kolom sektor ke wilayah (aman jika sudah ada)
-- -----------------------------------------------------------------------------
ALTER TABLE wilayah
  ADD COLUMN IF NOT EXISTS sektor ENUM(
    'Sektor Utara',
    'Sektor Timur',
    'Sektor Selatan',
    'Sektor Barat',
    'Sektor Tengah'
  ) NULL AFTER kode_wilayah;

-- -----------------------------------------------------------------------------
-- 2. Seed sektor per kemantren (14 kemantren → 5 sektor)
--    Pembagian berdasarkan wilayah operasional UPT PJU Kota Yogyakarta.
--    Sesuaikan dengan struktur regu aktual jika berbeda.
-- -----------------------------------------------------------------------------
UPDATE wilayah SET sektor = 'Sektor Utara'   WHERE nama_kemantren IN ('Jetis', 'Tegalrejo', 'Gondokusuman');
UPDATE wilayah SET sektor = 'Sektor Timur'   WHERE nama_kemantren IN ('Umbulharjo', 'Kotagede');
UPDATE wilayah SET sektor = 'Sektor Selatan' WHERE nama_kemantren IN ('Mergangsan', 'Mantrijeron', 'Kraton');
UPDATE wilayah SET sektor = 'Sektor Barat'   WHERE nama_kemantren IN ('Wirobrajan', 'Gedongtengen', 'Ngampilan');
UPDATE wilayah SET sektor = 'Sektor Tengah'  WHERE nama_kemantren IN ('Gondomanan', 'Pakualaman', 'Danurejan');

-- -----------------------------------------------------------------------------
-- 3. Buat tabel mutasi_aset
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mutasi_aset (
  id_mutasi        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_aset          INT          NOT NULL,
  id_petugas       INT          NULL,
  id_pemeliharaan  INT          NULL,

  jenis_mutasi     ENUM(
    'Pasang Baru',
    'Ganti Lampu',
    'Ganti Tiang',
    'Pindah Lokasi',
    'Pensiun / Bongkar',
    'Temuan Lapangan',
    'Stok Opname'
  ) NOT NULL,

  status_sebelum   ENUM('Menyala','Rusak','Dalam Pengerjaan') NULL,
  status_sesudah   ENUM('Menyala','Rusak','Dalam Pengerjaan') NULL,

  komponen         VARCHAR(100) NULL COMMENT 'Nama komponen yg dimutasi, misal: Lampu LED 50W',
  qty              SMALLINT     NOT NULL DEFAULT 1,

  lat_baru         DECIMAL(10,8) NULL COMMENT 'Koordinat baru jika pindah lokasi',
  lng_baru         DECIMAL(11,8) NULL,
  alamat_baru      VARCHAR(255)  NULL,

  keterangan       TEXT         NULL,
  foto_url         VARCHAR(255) NULL,

  tanggal_mutasi   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_mutasi_aset       FOREIGN KEY (id_aset)         REFERENCES aset_pju(id_aset)                       ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_mutasi_petugas    FOREIGN KEY (id_petugas)      REFERENCES pengguna(id_pengguna)                   ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_mutasi_pemeliharaan FOREIGN KEY (id_pemeliharaan) REFERENCES riwayat_pemeliharaan(id_pemeliharaan) ON DELETE SET NULL ON UPDATE CASCADE,

  INDEX idx_mutasi_aset    (id_aset),
  INDEX idx_mutasi_petugas (id_petugas),
  INDEX idx_mutasi_tanggal (tanggal_mutasi),
  INDEX idx_mutasi_jenis   (jenis_mutasi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Log mutasi & stok opname aset PJU';

SET FOREIGN_KEY_CHECKS = 1;

-- Verifikasi
SELECT 'Migration wilayah_mutasi selesai.' AS status;
SELECT nama_kemantren, sektor FROM wilayah ORDER BY sektor, nama_kemantren;
