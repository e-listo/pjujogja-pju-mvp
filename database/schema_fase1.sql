-- =====================================================================
-- SKEMA MIGRASI FASE 1 - PIJAR (pjujogja.id)
-- Penguatan Inventarisasi Jaringan Aset yang Responsif
-- Berdasarkan ERD Fase 1 - Sistem Manajemen Aset & Pemeliharaan PJU
-- Dasar hukum:
--   - Pergub DIY No. 25 Tahun 2019 (terminologi kemantren/kalurahan)
--   - Perda Kota Yogyakarta No. 4 Tahun 2020 (pembentukan kemantren)
--   - Perwal Kota Yogyakarta No. 37 Tahun 2023 (DPUPKP/UPT PJU)
--   - Perwal Kota Yogyakarta No. 50 Tahun 2022 (kategori jalan)
-- Target: MariaDB (cPanel Shared Hosting - Dewaweb)
-- Catatan: File ini MELENGKAPI schema.sql (MVP awal), bukan mengganti.
--          Eksekusi BERURUTAN — jangan lewati langkah.
-- Format kode_wilayah: PREFIX+ANGKA tanpa separator (contoh: UH1, GK3)
--   - Panjang tetap 3 karakter untuk semua 45 kelurahan (CHAR(3))
--   - 0 prefix collision, URL-safe, JS-safe, CSS-safe
--   - Angka mengikuti urutan romawi resmi dokumen pemerintah
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- LANGKAH 1: TABEL BARU — WILAYAH
-- Terminologi "kemantren" sesuai Pergub DIY No. 25/2019 dan
-- Perda Kota Yogyakarta No. 4/2020
-- =====================================================================
CREATE TABLE IF NOT EXISTS wilayah (
    id_wilayah      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nama_kemantren  VARCHAR(100) NOT NULL,
    nama_kelurahan  VARCHAR(100) NOT NULL,
    kode_wilayah    CHAR(3)      NOT NULL UNIQUE,  -- selalu tepat 3 karakter
    INDEX idx_kemantren (nama_kemantren)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO wilayah (kode_wilayah, nama_kemantren, nama_kelurahan) VALUES
('UH1', 'Umbulharjo',   'Giwangan'),
('UH2', 'Umbulharjo',   'Sorosutan'),
('UH3', 'Umbulharjo',   'Pandeyan'),
('UH4', 'Umbulharjo',   'Warungboto'),
('UH5', 'Umbulharjo',   'Tahunan'),
('UH6', 'Umbulharjo',   'Muja Muju'),
('UH7', 'Umbulharjo',   'Semaki'),
('GK1', 'Gondokusuman', 'Demangan'),
('GK2', 'Gondokusuman', 'Klitren'),
('GK3', 'Gondokusuman', 'Terban'),
('GK4', 'Gondokusuman', 'Kotabaru'),
('GK5', 'Gondokusuman', 'Baciro'),
('TR1', 'Tegalrejo',    'Karangwaru'),
('TR2', 'Tegalrejo',    'Kricak'),
('TR3', 'Tegalrejo',    'Bener'),
('TR4', 'Tegalrejo',    'Tegalrejo'),
('JT1', 'Jetis',        'Bumijo'),
('JT2', 'Jetis',        'Gowongan'),
('JT3', 'Jetis',        'Cokrodiningratan'),
('GT1', 'Gedongtengen', 'Sosromenduran'),
('GT2', 'Gedongtengen', 'Pringgokusuman'),
('NG1', 'Ngampilan',    'Ngampilan'),
('NG2', 'Ngampilan',    'Notoprajan'),
('WB1', 'Wirobrajan',   'Pakuncen'),
('WB2', 'Wirobrajan',   'Wirobrajan'),
('WB3', 'Wirobrajan',   'Patangpuluhan'),
('MJ1', 'Mantrijeron',  'Suryodiningratan'),
('MJ2', 'Mantrijeron',  'Gedongkiwo'),
('MJ3', 'Mantrijeron',  'Mantrijeron'),
('KT1', 'Kraton',       'Panembahan'),
('KT2', 'Kraton',       'Kadipaten'),
('KT3', 'Kraton',       'Patehan'),
('GM1', 'Gondomanan',   'Prawirodirjan'),
('GM2', 'Gondomanan',   'Ngupasan'),
('MG1', 'Mergangsan',   'Wirogunan'),
('MG2', 'Mergangsan',   'Keparakan'),
('MG3', 'Mergangsan',   'Brontokusuman'),
('DN1', 'Danurejan',    'Bausasran'),
('DN2', 'Danurejan',    'Tegalpanggung'),
('DN3', 'Danurejan',    'Suryatmajan'),
('PA1', 'Pakualaman',   'Gunungketur'),
('PA2', 'Pakualaman',   'Purwokinanti'),
('KG1', 'Kotagede',     'Rejowinangun'),
('KG2', 'Kotagede',     'Prenggan'),
('KG3', 'Kotagede',     'Purbayan');

-- =====================================================================
-- LANGKAH 2: TABEL BARU — PANEL_PJU
-- =====================================================================
CREATE TABLE IF NOT EXISTS panel_pju (
    id_panel        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_wilayah      INT UNSIGNED NOT NULL,
    kode_panel      VARCHAR(30)  NOT NULL UNIQUE,
    kapasitas_kwh   DECIMAL(8,2) DEFAULT NULL,
    latitude        DECIMAL(10,8) DEFAULT NULL,
    longitude       DECIMAL(11,8) DEFAULT NULL,
    status          ENUM('Aktif','Nonaktif','Rusak') NOT NULL DEFAULT 'Aktif',
    keterangan      TEXT DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_panel_wilayah FOREIGN KEY (id_wilayah)
        REFERENCES wilayah(id_wilayah) ON DELETE RESTRICT,
    INDEX idx_panel_wilayah (id_wilayah),
    INDEX idx_panel_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- LANGKAH 3: TABEL BARU — REGU
-- 4 regu sesuai pembagian 4 sektor UPT PJU Kota Yogyakarta
-- =====================================================================
CREATE TABLE IF NOT EXISTS regu (
    id_regu         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nama_regu       VARCHAR(100) NOT NULL,
    sektor          ENUM('Sektor 1','Sektor 2','Sektor 3','Sektor 4') NOT NULL,
    keterangan_area TEXT DEFAULT NULL,
    status_aktif    TINYINT(1)   NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO regu (nama_regu, sektor, keterangan_area) VALUES
('Regu Pelaksana 1', 'Sektor 1', 'Wilayah barat laut: Tegalrejo, Jetis, Gedongtengen, Ngampilan'),
('Regu Pelaksana 2', 'Sektor 2', 'Wilayah timur laut: Gondokusuman, Danurejan, Pakualaman, Gondomanan'),
('Regu Pelaksana 3', 'Sektor 3', 'Wilayah tenggara: Mergangsan, Umbulharjo, Kotagede'),
('Regu Pelaksana 4', 'Sektor 4', 'Wilayah barat daya: Wirobrajan, Mantrijeron, Kraton');

-- =====================================================================
-- LANGKAH 4: ALTER TABLE pengguna
-- Tambah: id_regu, no_hp, role koordinator
-- =====================================================================
ALTER TABLE pengguna
    ADD COLUMN id_regu  INT UNSIGNED DEFAULT NULL AFTER password_hash,
    ADD COLUMN no_hp    VARCHAR(20)  DEFAULT NULL AFTER id_regu,
    MODIFY COLUMN peran ENUM('admin','koordinator','teknisi') NOT NULL DEFAULT 'teknisi',
    ADD CONSTRAINT fk_pengguna_regu FOREIGN KEY (id_regu)
        REFERENCES regu(id_regu) ON DELETE SET NULL;

UPDATE pengguna SET id_regu = 1 WHERE username = 'teknisi1';

-- =====================================================================
-- LANGKAH 5: ALTER TABLE aset_pju
-- Tambah: id_wilayah, id_panel, jenis_tiang, tinggi_meter, foto_url
-- =====================================================================
ALTER TABLE aset_pju
    ADD COLUMN id_wilayah   INT UNSIGNED DEFAULT NULL AFTER kode_aset,
    ADD COLUMN id_panel     INT UNSIGNED DEFAULT NULL AFTER id_wilayah,
    ADD COLUMN jenis_tiang  VARCHAR(50)  DEFAULT NULL AFTER tanggal_pasang,
    ADD COLUMN tinggi_meter DECIMAL(4,1) DEFAULT NULL AFTER jenis_tiang,
    ADD COLUMN foto_url     VARCHAR(255) DEFAULT NULL AFTER tinggi_meter,
    ADD CONSTRAINT fk_aset_wilayah FOREIGN KEY (id_wilayah)
        REFERENCES wilayah(id_wilayah) ON DELETE SET NULL,
    ADD CONSTRAINT fk_aset_panel FOREIGN KEY (id_panel)
        REFERENCES panel_pju(id_panel) ON DELETE SET NULL,
    ADD INDEX idx_wilayah (id_wilayah),
    ADD INDEX idx_panel (id_panel);

-- =====================================================================
-- LANGKAH 6: TABEL BARU — LAMPU
-- Memisahkan detail komponen lampu dari aset_pju
-- =====================================================================
CREATE TABLE IF NOT EXISTS lampu (
    id_lampu        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_aset         INT UNSIGNED NOT NULL,
    jenis_lampu     VARCHAR(50)  NOT NULL,
    daya_watt       SMALLINT UNSIGNED DEFAULT NULL,
    merk            VARCHAR(100) DEFAULT NULL,
    tahun_pasang    YEAR         DEFAULT NULL,
    status_lampu    ENUM('Menyala','Mati','Redup','Rusak') NOT NULL DEFAULT 'Menyala',
    keterangan      TEXT DEFAULT NULL,
    CONSTRAINT fk_lampu_aset FOREIGN KEY (id_aset)
        REFERENCES aset_pju(id_aset) ON DELETE CASCADE,
    INDEX idx_lampu_aset (id_aset),
    INDEX idx_lampu_status (status_lampu)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO lampu (id_aset, jenis_lampu, daya_watt, tahun_pasang)
SELECT id_aset, IFNULL(jenis_lampu, 'LED'), watt, YEAR(tanggal_pasang)
FROM aset_pju
WHERE jenis_lampu IS NOT NULL OR watt IS NOT NULL;

-- =====================================================================
-- LANGKAH 7: TABEL BARU — LAPORAN_KERUSAKAN
-- Dipisah dari laporan_kerja agar lebih fokus per entitas
-- =====================================================================
CREATE TABLE IF NOT EXISTS laporan_kerusakan (
    id_laporan          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_aset             INT UNSIGNED NOT NULL,
    id_pengguna         INT UNSIGNED DEFAULT NULL,
    deskripsi_kerusakan TEXT         NOT NULL,
    foto_url            VARCHAR(255) DEFAULT NULL,
    sumber_laporan      ENUM('Lapangan','JSS','Masyarakat','Patroli') NOT NULL DEFAULT 'Lapangan',
    status_laporan      ENUM('Baru','Diproses','Selesai','Ditolak')   NOT NULL DEFAULT 'Baru',
    tanggal_lapor       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lapker_aset FOREIGN KEY (id_aset)
        REFERENCES aset_pju(id_aset) ON DELETE CASCADE,
    CONSTRAINT fk_lapker_pengguna FOREIGN KEY (id_pengguna)
        REFERENCES pengguna(id_pengguna) ON DELETE SET NULL,
    INDEX idx_lapker_status (status_laporan),
    INDEX idx_lapker_tanggal (tanggal_lapor),
    INDEX idx_lapker_aset (id_aset)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO laporan_kerusakan
    (id_aset, id_pengguna, deskripsi_kerusakan, sumber_laporan, status_laporan, tanggal_lapor)
SELECT
    id_aset,
    id_teknisi,
    IFNULL(catatan, 'Migrasi dari laporan_kerja MVP'),
    'Lapangan',
    CASE status
        WHEN 'Baru'             THEN 'Baru'
        WHEN 'Dalam Pengerjaan' THEN 'Diproses'
        WHEN 'Selesai'          THEN 'Selesai'
        ELSE 'Baru'
    END,
    tanggal_lapor
FROM laporan_kerja;

-- =====================================================================
-- LANGKAH 8: TABEL BARU — RIWAYAT_PEMELIHARAAN
-- =====================================================================
CREATE TABLE IF NOT EXISTS riwayat_pemeliharaan (
    id_pemeliharaan     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_aset             INT UNSIGNED NOT NULL,
    id_regu             INT UNSIGNED DEFAULT NULL,
    id_pengguna         INT UNSIGNED DEFAULT NULL,
    id_laporan          INT UNSIGNED DEFAULT NULL,
    jenis_pekerjaan     ENUM('Perbaikan','Penggantian Lampu','Perawatan Rutin',
                             'Penggantian Tiang','Pengecekan Panel','Lainnya')
                        NOT NULL DEFAULT 'Perbaikan',
    deskripsi_pekerjaan TEXT         DEFAULT NULL,
    foto_sebelum        VARCHAR(255) DEFAULT NULL,
    foto_sesudah        VARCHAR(255) DEFAULT NULL,
    status_pekerjaan    ENUM('Dalam Pengerjaan','Selesai','Ditunda') NOT NULL DEFAULT 'Dalam Pengerjaan',
    tanggal_pengerjaan  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_riwayat_aset FOREIGN KEY (id_aset)
        REFERENCES aset_pju(id_aset) ON DELETE CASCADE,
    CONSTRAINT fk_riwayat_regu FOREIGN KEY (id_regu)
        REFERENCES regu(id_regu) ON DELETE SET NULL,
    CONSTRAINT fk_riwayat_pengguna FOREIGN KEY (id_pengguna)
        REFERENCES pengguna(id_pengguna) ON DELETE SET NULL,
    CONSTRAINT fk_riwayat_laporan FOREIGN KEY (id_laporan)
        REFERENCES laporan_kerusakan(id_laporan) ON DELETE SET NULL,
    INDEX idx_riwayat_aset (id_aset),
    INDEX idx_riwayat_tanggal (tanggal_pengerjaan),
    INDEX idx_riwayat_status (status_pekerjaan)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO riwayat_pemeliharaan
    (id_aset, id_pengguna, jenis_pekerjaan, deskripsi_pekerjaan,
     foto_sesudah, status_pekerjaan, tanggal_pengerjaan)
SELECT
    id_aset,
    id_teknisi,
    IFNULL(tindakan_perbaikan, 'Perbaikan'),
    catatan,
    foto_bukti,
    CASE status
        WHEN 'Selesai' THEN 'Selesai'
        ELSE 'Dalam Pengerjaan'
    END,
    IFNULL(tanggal_selesai, tanggal_lapor)
FROM laporan_kerja;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- SELESAI — PIJAR schema_fase1.sql | v1.0 | 2026
-- Format kode_wilayah: CHAR(3) — PREFIX+ANGKA (UH1, GK3, dst.)
-- Tabel aktif setelah migrasi:
--   wilayah, panel_pju, regu,
--   pengguna (updated), aset_pju (updated),
--   lampu, laporan_kerusakan, riwayat_pemeliharaan,
--   stok_pins (tidak diubah), laporan_kerja (tidak dihapus)
-- =====================================================================
