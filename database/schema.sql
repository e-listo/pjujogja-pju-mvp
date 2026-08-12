-- =====================================================================
-- SKEMA DATABASE MVP PJU JOGJA (pjujogja.id)
-- Kategori jalan sesuai Perwal Kota Yogyakarta No. 50/2022:
--   Pasal 1 ayat 2 & Pasal 33: Jalan Kota, Jalan Lingkungan, Jalan Lingkungan Kampung
--   Pasal 1 ayat 1 & Pasal 13: Lainnya (Taman/Makam/Sorot Sungai/Hias-Budaya)
-- Target: MariaDB (cPanel Shared Hosting - Dewaweb)
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS pengguna (
    id_pengguna     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nama_lengkap    VARCHAR(100) NOT NULL,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    peran           ENUM('admin', 'teknisi') NOT NULL DEFAULT 'teknisi',
    status_aktif    TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS aset_pju (
    id_aset             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    kode_aset           VARCHAR(30)  NOT NULL UNIQUE,
    alamat              VARCHAR(255) NOT NULL,
    lokasi_lat          DECIMAL(10,8) NOT NULL,
    lokasi_lng          DECIMAL(11,8) NOT NULL,
    kategori_jalan      ENUM('Jalan Kota','Jalan Lingkungan','Jalan Lingkungan Kampung','Lainnya')
                        NOT NULL DEFAULT 'Jalan Lingkungan',
    sub_kategori_lainnya ENUM('Taman','Makam','Sorot Sungai','Hias/Budaya') DEFAULT NULL,
    jenis_lampu         VARCHAR(50)  DEFAULT NULL,
    watt                SMALLINT UNSIGNED DEFAULT NULL,
    status              ENUM('Menyala','Rusak','Dalam Pengerjaan') NOT NULL DEFAULT 'Menyala',
    tanggal_pasang      DATE DEFAULT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_koordinat (lokasi_lat, lokasi_lng),
    CONSTRAINT chk_sub_kategori CHECK (
        (kategori_jalan = 'Lainnya' AND sub_kategori_lainnya IS NOT NULL) OR
        (kategori_jalan <> 'Lainnya' AND sub_kategori_lainnya IS NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stok_pins (
    id_komponen     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nama_komponen   VARCHAR(100) NOT NULL,
    kategori        VARCHAR(50)  DEFAULT NULL,
    satuan          VARCHAR(20)  NOT NULL DEFAULT 'pcs',
    stok_qty        INT NOT NULL DEFAULT 0,
    stok_minimum    INT NOT NULL DEFAULT 5,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (stok_qty >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS laporan_kerja (
    id_laporan               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_aset                  INT UNSIGNED NOT NULL,
    id_teknisi                INT UNSIGNED DEFAULT NULL,
    tanggal_lapor             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tanggal_selesai           DATETIME DEFAULT NULL,
    kategori_jalan_snap       ENUM('Jalan Kota','Jalan Lingkungan','Jalan Lingkungan Kampung','Lainnya')
                              NOT NULL,
    sub_kategori_lainnya_snap ENUM('Taman','Makam','Sorot Sungai','Hias/Budaya') DEFAULT NULL,
    status                    ENUM('Baru','Dalam Pengerjaan','Selesai') NOT NULL DEFAULT 'Baru',
    tindakan_perbaikan        VARCHAR(100) DEFAULT NULL,
    id_komponen_pins          INT UNSIGNED DEFAULT NULL,
    qty_komponen              INT UNSIGNED DEFAULT 1,
    foto_bukti                VARCHAR(255) DEFAULT NULL,
    catatan                   TEXT DEFAULT NULL,
    created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_laporan_aset FOREIGN KEY (id_aset) REFERENCES aset_pju(id_aset) ON DELETE CASCADE,
    CONSTRAINT fk_laporan_teknisi FOREIGN KEY (id_teknisi) REFERENCES pengguna(id_pengguna) ON DELETE SET NULL,
    CONSTRAINT fk_laporan_komponen FOREIGN KEY (id_komponen_pins) REFERENCES stok_pins(id_komponen) ON DELETE SET NULL,
    INDEX idx_status_lap (status),
    INDEX idx_tanggal_lapor (tanggal_lapor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO stok_pins (nama_komponen, kategori, satuan, stok_qty, stok_minimum) VALUES
('Lampu LED 50W', 'Lampu', 'pcs', 25, 5),
('Lampu LED 100W', 'Lampu', 'pcs', 15, 5),
('Fitting Lampu', 'Aksesoris', 'pcs', 40, 10),
('Kabel NYA 2.5mm', 'Kabel', 'meter', 200, 50),
('MCB 6A', 'Panel', 'pcs', 20, 5);

INSERT INTO pengguna (nama_lengkap, username, password_hash, peran) VALUES
('Admin UPT PJU', 'admin', '$2b$12$CHANGE_ME_HASH', 'admin'),
('Teknisi Regu 1', 'teknisi1', '$2b$12$CHANGE_ME_HASH', 'teknisi');

INSERT INTO aset_pju (kode_aset, alamat, lokasi_lat, lokasi_lng, kategori_jalan, sub_kategori_lainnya, jenis_lampu, watt, status) VALUES
('PJU-YK-0001', 'Jl. Malioboro (Jalan Kota)', -7.79300000, 110.36530000, 'Jalan Kota', NULL, 'LED', 100, 'Rusak'),
('PJU-YK-0002', 'Jl. Perumnas Condongcatur (Jalan Lingkungan)', -7.76900000, 110.40100000, 'Jalan Lingkungan', NULL, 'LED', 50, 'Menyala'),
('PJU-YK-0003', 'Gang RT 05 Prawirotaman (Jalan Lingkungan Kampung)', -7.81700000, 110.36400000, 'Jalan Lingkungan Kampung', NULL, 'LED', 30, 'Menyala'),
('PJU-YK-0004', 'Taman Pintar Yogyakarta', -7.80170000, 110.36850000, 'Lainnya', 'Taman', 'LED', 40, 'Menyala'),
('PJU-YK-0005', 'TPU Pracimaloyo (Makam)', -7.82100000, 110.35200000, 'Lainnya', 'Makam', 'LED', 20, 'Rusak'),
('PJU-YK-0006', 'Sorot Sungai Code - Jembatan Sayidan', -7.79900000, 110.37200000, 'Lainnya', 'Sorot Sungai', 'LED', 60, 'Menyala');
