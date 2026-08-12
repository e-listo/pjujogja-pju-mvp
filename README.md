# PJU Jogja — Sistem Dashboard Manajemen Aset & Pemeliharaan PJU

Sistem dashboard manajemen aset, pemeliharaan Penerangan Jalan Umum (PJU), dan integrasi inventaris (PINS) untuk operasional UPT PJU Kota Yogyakarta (DPUPKP).

Dirancang khusus untuk ekosistem **shared hosting** (Dewaweb, cPanel, LiteSpeed, Python App, MariaDB) — ringan dan praktikal, tanpa dependensi server khusus.

## Domain & Subdomain

- `pjujogja.id` — domain utama
- `admin.pjujogja.id` — dashboard admin (peta + task list)
- `api.pjujogja.id` — REST API backend (Flask via Passenger WSGI)
- `pins.pjujogja.id` — integrasi sistem inventaris PINS

## Tech Stack

- **Backend**: Python (Flask) + Flask-SQLAlchemy + PyMySQL
- **Database**: MariaDB
- **Frontend**: HTML/CSS/JS + Leaflet.js (peta geospasial), responsif/mobile-first
- **Deployment**: cPanel Setup Python App (Passenger WSGI)

## Struktur Direktori

```
.
├── app.py                 # Entry point Flask (REST API)
├── config.py              # Konfigurasi environment & bobot prioritas
├── models.py              # Model SQLAlchemy (AsetPJU, LaporanKerja, StokPins, Pengguna)
├── passenger_wsgi.py      # WSGI entry point untuk cPanel Python App
├── requirements.txt       # Dependensi Python
├── database/
│   └── schema.sql         # DDL MariaDB (3 tabel utama + tabel pendukung)
├── frontend/
│   ├── admin/index.html   # Dashboard admin (peta Leaflet + task list)
│   └── lapangan/form.html # Form update status regu lapangan (kompresi foto client-side)
└── docs/
    └── panduan_deployment_fase1.md  # Panduan setup cPanel & roadmap Fase 2-4
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
- Peta geospasial dasar (Leaflet.js) dengan marker warna real-time (merah/kuning/hijau)
- Sistem ticketing & task list dengan prioritas linier
- Form update status regu lapangan (dropdown tindakan, kompresi foto client-side <300KB)
- Integrasi dasar PINS (pemotongan stok otomatis saat komponen diganti)

**Di luar scope (fase ini):**
- Algoritma prediksi kerusakan (preventive maintenance / Fuzzy-PID)
- Mode offline penuh (full local-sync)
- Portal pelaporan warga publik

## Setup Lokal

```bash
pip install -r requirements.txt
cp .env.example .env   # isi kredensial database Anda
python app.py
```

Lihat `docs/panduan_deployment_fase1.md` untuk panduan lengkap deployment ke cPanel/Dewaweb.

## Lisensi & Kerahasiaan

Repository ini bersifat **privat** karena menyangkut infrastruktur pemerintah. Jangan commit kredensial database asli — gunakan `.env` (sudah di-gitignore) berdasarkan `.env.example`.
