<!-- HERO -->
<p align="center">
  <img src="https://pjujogja.id/images/pijar_square.png" alt="Logo PIJAR" width="96">
</p>

<h1 align="center">PIJAR</h1>
<p align="center">
  <sub><b>Penguatan Inventarisasi Jaringan Aset yang Responsif</b></sub>
</p>

<p align="center">
  ────────────────────────
</p>

<p align="center">
  <em><b>“Urip Kuwi Urup”</b></em>
</p>
<p align="center">
  <b>MENYALAKAN DATA &nbsp;&middot;&nbsp; MENERANGI PELAYANAN</b>
</p>

---

Sistem dashboard manajemen aset, pemeliharaan Penerangan Jalan Umum (PJU), dan integrasi inventaris (PINS) untuk operasional UPT PJU Kota Yogyakarta (DPUPKP).

Dirancang khusus untuk ekosistem **shared hosting** (Dewaweb, cPanel, LiteSpeed, Python App, MariaDB) — ringan dan praktikal, tanpa dependensi server khusus.

## Domain & Subdomain

| Subdomain | Fungsi |
|---|---|
| `pjujogja.id` | Domain utama |
| `admin.pjujogja.id` | Dashboard admin PIJAR (peta + task list + login) |
| `api.pjujogja.id` | REST API backend (Flask via Passenger WSGI) |
| `pins.pjujogja.id` | Integrasi sistem inventaris PINS |

## Tech Stack

- **Backend**: Python (Flask) + Flask-SQLAlchemy + PyMySQL
- **Database**: MariaDB
- **Frontend**: HTML/CSS/JS + Leaflet.js (peta geospasial), responsif/mobile-first
- **Deployment**: cPanel Setup Python App (Passenger WSGI)

## Struktur Direktori

```
.
├── app.py                      # Entry point Flask (REST API)
├── auth_routes.py              # Route autentikasi (login/logout, JWT)
├── config.py                   # Konfigurasi environment & bobot prioritas
├── models.py                   # Model SQLAlchemy (AsetPJU, LaporanKerja, StokPins, Pengguna)
├── passenger_wsgi.py           # WSGI entry point untuk cPanel Python App
├── requirements.txt            # Dependensi Python
├── database/
│   ├── schema.sql              # DDL MVP awal (tabel dasar)
│   └── schema_fase1.sql        # Migrasi Fase 1 ERD PIJAR — eksekusi SETELAH schema.sql
├── frontend/
│   ├── admin/
│   │   ├── login.html          # Halaman login PIJAR (JWT, redirect ke index)
│   │   └── index.html          # Dashboard admin (peta Leaflet + task list)
│   └── lapangan/
│       ├── lapor.html          # Form lapor kerusakan baru (dari regu/masyarakat/JSS)
│       └── form.html           # Form update status selesai perbaikan + potong stok PINS
└── docs/
    └── panduan_deployment_fase1.md  # Panduan setup cPanel & roadmap Fase 2-4
```

> **Catatan alur lapangan:** `lapor.html` → input kerusakan baru → tiket masuk sistem → `form.html` → regu tandai tiket selesai + stok PINS terpotong otomatis.

## Database Schema

### `schema.sql` — MVP Awal
Tabel dasar untuk operasional awal:

| Tabel | Keterangan |
|---|---|
| `aset_pju` | Data titik lampu PJU |
| `laporan_kerja` | Laporan & task pemeliharaan |
| `stok_pins` | Inventaris komponen/suku cadang |
| `pengguna` | Akun pengguna sistem |

### `schema_fase1.sql` — Migrasi Fase 1 ERD PIJAR
File ini **melengkapi** `schema.sql`, bukan mengganti. Eksekusi berurutan setelah `schema.sql`.

| Tabel | Keterangan |
|---|---|
| `wilayah` *(baru)* | 45 kelurahan Kota Yogyakarta — kode `CHAR(3)` format `UH1`–`KG3` |
| `panel_pju` *(baru)* | Gardu/panel distribusi listrik PJU per wilayah |
| `regu` *(baru)* | 4 regu pelaksana sesuai 4 sektor UPT PJU |
| `lampu` *(baru)* | Komponen lampu per tiang (dipisah dari `aset_pju`) |
| `laporan_kerusakan` *(baru)* | Laporan kerusakan (sumber: Lapangan, JSS, Masyarakat, Patroli) |
| `riwayat_pemeliharaan` *(baru)* | Log pekerjaan + foto sebelum/sesudah |
| `pengguna` *(dimodifikasi)* | Tambah kolom `id_regu`, `no_hp`, role `koordinator` |
| `aset_pju` *(dimodifikasi)* | Tambah kolom `id_wilayah`, `id_panel`, `jenis_tiang`, `tinggi_meter`, `foto_url` |

### Format `kode_wilayah`

Menggunakan format **`CHAR(3)`**: 2 huruf prefix kemantren + 1 angka urut kelurahan.

```
UH1 = Kemantren Umbulharjo, Kelurahan Giwangan (Umbulharjo I)
UH7 = Kemantren Umbulharjo, Kelurahan Semaki   (Umbulharjo VII)
GK1 = Kemantren Gondokusuman, Kelurahan Demangan
KG3 = Kemantren Kotagede, Kelurahan Purbayan
```

Keunggulan format ini: panjang seragam (efisien di index MariaDB), 0 prefix collision, URL/JS/CSS/shell-safe, angka mengikuti urutan romawi dokumen resmi (Pergub DIY No. 25/2019).

### ERD Fase 1 — Relasi Antar Entitas

```
WILAYAH ──< PANEL_PJU
WILAYAH ──< ASET_PJU
PANEL_PJU ──< ASET_PJU
ASET_PJU ──< LAMPU
ASET_PJU ──< LAPORAN_KERUSAKAN
ASET_PJU ──< RIWAYAT_PEMELIHARAAN
REGU ──< PENGGUNA
REGU ──< RIWAYAT_PEMELIHARAAN
PENGGUNA ──< LAPORAN_KERUSAKAN
PENGGUNA ──< RIWAYAT_PEMELIHARAAN
LAPORAN_KERUSAKAN ──o RIWAYAT_PEMELIHARAAN
```

## Kategori Jalan (Perwal Kota Yogyakarta No. 50 Tahun 2022)

Kategori jalan **TIDAK** mengikuti klasifikasi fungsi jalan Kemenhub (Arteri/Kolektor/Lokal), melainkan disesuaikan dengan kearifan lokal sesuai Perwal Yogyakarta No. 50/2022:

| Kategori | Dasar Pasal | Bobot Prioritas |
|---|---|---|
| Jalan Kota | Pasal 33 (tiang ≥ 7.000 mm) | 3 |
| Jalan Lingkungan | Pasal 33 (tiang ≤ 7.000 mm) | 2 |
| Jalan Lingkungan Kampung | Pasal 33 (tiang ≤ 4.000 mm) | 1 |
| Lainnya (Taman/Makam/Sorot Sungai/Hias-Budaya) | Pasal 1 ayat 1 & Pasal 13 | 1 |

Formula skor prioritas tiket: `skor = bobot_kategori_jalan + bobot_durasi_mati` (dihitung real-time, tidak disimpan statis).

## MVP Scope

**Termasuk:**
- Halaman login PIJAR (JWT, auto-redirect jika token valid)
- Peta geospasial dasar (Leaflet.js) dengan marker warna real-time (merah/kuning/hijau)
- Sistem ticketing & task list dengan prioritas linier
- Form lapor kerusakan baru dari regu lapangan/masyarakat/JSS
- Form update status selesai perbaikan (kompresi foto client-side <300KB, potong stok PINS otomatis)
- Form tambah aset PJU baru oleh Admin/Koordinator
- Integrasi dasar PINS (pemotongan stok otomatis saat komponen diganti)
- Manajemen wilayah (45 kelurahan, 14 kemantren, 4 sektor regu)

**Di luar scope (fase ini):**
- Algoritma prediksi kerusakan (preventive maintenance / Fuzzy-PID)
- Mode offline penuh (full local-sync)
- Portal pelaporan warga publik

## Setup Lokal

```bash
pip install -r requirements.txt
cp .env.example .env        # isi kredensial database Anda
```

**Inisialisasi database — eksekusi BERURUTAN:**

```bash
# Langkah 1: Skema MVP dasar
mysql -u root -p nama_database < database/schema.sql

# Langkah 2: Migrasi Fase 1 ERD PIJAR (jalankan SETELAH schema.sql)
mysql -u root -p nama_database < database/schema_fase1.sql
```

```bash
# Jalankan server lokal
python app.py
```

Lihat `docs/panduan_deployment_fase1.md` untuk panduan lengkap deployment ke cPanel/Dewaweb.

## Dasar Hukum

| Regulasi | Relevansi |
|---|---|
| Pergub DIY No. 25 Tahun 2019 | Terminologi kemantren & kalurahan |
| Perda Kota Yogyakarta No. 4 Tahun 2020 | Pembentukan kemantren |
| Perwal Kota Yogyakarta No. 37 Tahun 2023 | Tugas & fungsi DPUPKP / UPT PJU |
| Perwal Kota Yogyakarta No. 50 Tahun 2022 | Kategori & spesifikasi jalan |

## Lisensi & Kerahasiaan

Repository ini bersifat **privat** karena menyangkut infrastruktur pemerintah. Jangan commit kredensial database asli — gunakan `.env` (sudah di-gitignore) berdasarkan `.env.example`.

---

<p align="center">&copy; UPT Penerangan Jalan Umum &middot; Dinas PUPKP Kota Yogyakarta</p>
