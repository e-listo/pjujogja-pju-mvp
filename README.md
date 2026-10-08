<!-- HERO -->
<p align="center">
  <img src="https://pjujogja.id/images/pijar_square.png" alt="Logo PIJAR" width="96">
</p>
<h1 align="center">PIJAR</h1>
<p align="center"><sub><b>PENGUATAN INVENTARISASI JARINGAN ASET YANG RESPONSIF</b></sub></p>
<p align="center">────────────────────────</p>
<p align="center"><em><b>“Urip Kuwi Urup”</b></em></p>
<p align="center"><b>MENYALAKAN DATA &nbsp;&middot;&nbsp; MENERANGI PELAYANAN</b></p>

---

Sistem dashboard manajemen aset, pemeliharaan Penerangan Jalan Umum (PJU), dan integrasi inventaris (PINS) untuk operasional UPT PJU Kota Yogyakarta (DPUPKP).

Dirancang untuk shared hosting Dewaweb/cPanel/LiteSpeed dengan Python App dan MariaDB: ringan, praktikal, dan responsif untuk kantor maupun tablet/smartphone lapangan.

## Status proyek

Diperbarui 8 Oktober 2026. Acuan kode: main setelah PR #28, commit a257ef7e40bc2ea2f3158bd2a1006918bcbed188.

- Bulk import Excel aset dan lampu tersedia: template, pratinjau, simpan atomik, dan penolakan kode duplikat tanpa menimpa. CSV masih ditunda.
- Backend manajemen pengguna tersedia (PR #22/#23), berikut frontend pengguna.html (PR #26).
- Alias peran regu pada decorator dipetakan ke teknisi (PR #25); akun tetap memakai enum admin, koordinator, teknisi.
- Sidebar memuat menu Pengguna khusus admin, kotak akun navy-oranye, serta drawer mobile (PR #27).
- Kepanjangan PIJAR dan teks footer login/sidebar disamakan (PR #28).

Riwayat, hasil uji, temuan, dan pekerjaan lanjutan: [Catatan Progres](docs/CATATAN-PROGRES.md). Kode merged tidak otomatis berarti sudah ter-deploy.

## Domain dan subdomain

| Domain | Fungsi |
|---|---|
| pjujogja.id | Domain utama |
| admin.pjujogja.id | Dashboard admin PIJAR |
| api.pjujogja.id | REST API Flask melalui Passenger WSGI |
| pins.pjujogja.id | Konteks integrasi inventaris PINS; jangan menganggap seluruh sinkronisasi lintas sistem telah tersedia |

Frontend memanggil https://api.pjujogja.id. Login API berada di POST /api/auth/login, bukan pada subdomain admin.

## Tech stack

- Backend: Python, Flask, Flask-SQLAlchemy, PyMySQL, JWT.
- Database: MariaDB.
- Frontend: HTML/CSS/JavaScript dan Leaflet.js, responsif.
- Deployment: cPanel Setup Python App, Passenger WSGI, LiteSpeed.
- CI: Playwright/browser, integration, production-schema MariaDB 10.6/10.11, serta syntax-check sesuai pemicu workflow.

## Fitur tersedia

### Aset dan pemeliharaan

- Login JWT, dashboard peta dan task list, serta prioritas tiket.
- Daftar/detail/tambah/ubah aset, lampu, wilayah, regu, laporan, pemeliharaan, dan mutasi sesuai endpoint dan izin yang tersedia.
- Bulk import Excel aset/lampu dengan pratinjau dan konfirmasi simpan; kode duplikat ditolak, bukan diperbarui.
- Unduh template memakai Response berisi byte untuk menghindari galat fileno LiteSpeed.
- Form lapor kerusakan dan penanganan lapangan, foto pekerjaan, serta pengelolaan komponen/stok PINS pada alur yang mendukungnya.

Alur konseptual: laporan kerusakan -> tiket -> pekerjaan -> penyelesaian. Pemotongan stok bergantung endpoint dan data komponen; jangan menganggap semua jalur form memiliki otomatisasi yang sama. Detail implementasi tetap mengacu kode backend.

### Manajemen pengguna

- Halaman pengguna.html: daftar, cari, filter peran/status, paginasi, tambah/ubah, reset password, aktif/nonaktif.
- Profil akun: nama lengkap, username, peran, regu opsional, no. HP, dan status aktif.
- Tidak ada hapus akun; nonaktifkan agar relasi dan riwayat tetap terjaga.
- Admin tidak dapat menonaktifkan atau mengubah peran akunnya sendiri.
- Backend memeriksa akun dan peran terbaru dari database pada setiap permintaan terlindungi.
- Password di-hash dengan Werkzeug; jangan memasukkan password polos atau hash dari sistem lain langsung ke database.
- Audit perubahan pengguna dicatat di log aplikasi. Ganti password sendiri tersedia di backend; halaman pengguna saat ini menyediakan reset oleh admin.

| Peran | Ringkasan |
|---|---|
| admin | Manajemen pengguna dan akses operasional sesuai decorator backend |
| koordinator | Operasional yang diizinkan backend; tidak memiliki akses manajemen pengguna |
| teknisi | Pelaksana lapangan; tidak memiliki akses manajemen pengguna atau bulk import |

Regu adalah kelompok kerja, bukan peran login terpisah. Menu yang disembunyikan di browser bukan kontrol keamanan; API adalah penentu izin.

### Identitas dan navigasi

- Header sidebar dan login: PENGUATAN INVENTARISASI JARINGAN ASET YANG RESPONSIF.
- Footer login/sidebar/mobile: © [tahun] UPT Penerangan Jalan Umum · Dinas PUPKP Kota Yogyakarta, dengan tahun otomatis.
- Sidebar desktop 224 px; pada lebar <=768 px menggunakan navigasi bawah dan drawer Lainnya.
- Menu Pengguna tersedia untuk admin. Drawer mendukung tombol tutup, overlay, Escape, dan fokus keyboard.

## Struktur direktori utama

```text
.
├── app.py                          # REST API Flask
├── auth_routes.py                  # JWT dan manajemen pengguna
├── aset_bulk_routes.py             # HTTP bulk import/template
├── aset_bulk_service.py            # Validasi dan pemrosesan impor
├── config.py                       # Konfigurasi environment
├── models.py                       # Model SQLAlchemy
├── passenger_wsgi.py               # WSGI cPanel
├── requirements.txt
├── deploy-production.sh            # Preflight/dry-run/apply backend
├── deploy.sh                       # Skrip deploy lain; baca sebelum digunakan
├── database/                       # SQL skema/migrasi; cocokkan dengan model terbaru
├── frontend/
│   ├── admin/
│   │   ├── login.html
│   │   ├── index.html
│   │   ├── aset.html
│   │   ├── tambah_aset.html
│   │   ├── laporan.html
│   │   ├── pemeliharaan.html
│   │   ├── wilayah.html
│   │   ├── regu.html
│   │   ├── pengguna.html
│   │   └── js/                     # auth.js, sidebar.js, aset-bulk.js, detail-deeplink.js
│   └── lapangan/                   # lapor.html dan form.html
├── tests/
├── .github/workflows/
└── docs/
    ├── CATATAN-PROGRES.md
    └── panduan_deployment_fase1.md  # Panduan historis Fase 1; baca bersama catatan terkini
```

## Database: konteks awal dan migrasi

Panduan awal menggunakan schema.sql lalu schema_fase1.sql. Skema Fase 1 melengkapi skema MVP, bukan menggantikannya. Ini bukan jaminan bahwa dua berkas tersebut saja mencukupi model terkini; tinjau seluruh SQL/migrasi dan CI production-schema sebelum instalasi baru atau upgrade.

| Kelompok | Entitas utama |
|---|---|
| MVP awal | aset_pju, laporan_kerja, stok_pins, pengguna |
| Fase 1 | wilayah, panel_pju, regu, lampu, laporan_kerusakan, riwayat_pemeliharaan |
| Model lanjutan | KategoriPJU dan MutasiAset; periksa definisi dan skema aktual di repo |

Data referensi awal proyek mencakup 45 kelurahan, 14 kemantren, dan 4 sektor/regu; ini bukan hitungan live database.

Kode wilayah memakai CHAR(3): dua huruf kemantren dan satu angka urut kelurahan. Contoh referensi awal: UH1 Giwangan, UH7 Semaki, GK1 Demangan, KG3 Purbayan. Cocokkan dengan seed/data wilayah yang digunakan saat deploy.

Relasi konseptual Fase 1:

```text
WILAYAH -> PANEL_PJU, ASET_PJU
PANEL_PJU -> ASET_PJU
ASET_PJU -> LAMPU, LAPORAN_KERUSAKAN, RIWAYAT_PEMELIHARAAN
REGU -> PENGGUNA, RIWAYAT_PEMELIHARAAN
PENGGUNA -> LAPORAN_KERUSAKAN, RIWAYAT_PEMELIHARAAN
LAPORAN_KERUSAKAN -> RIWAYAT_PEMELIHARAAN (relasi opsional)
```

## Kategori jalan dan prioritas

Kategori operasional proyek: Jalan Kota, Jalan Lingkungan, Jalan Lingkungan Kampung, dan Lainnya (Taman/Makam/Sorot Sungai/Hias-Budaya). Kategori ini bukan klasifikasi Arteri/Kolektor/Lokal.

Bobot awal proyek: Jalan Kota 3; Jalan Lingkungan 2; Jalan Lingkungan Kampung 1; Lainnya 1. Formula prioritas: skor = bobot_kategori_jalan + bobot_durasi_mati. Cocokkan nilai aktif dan pemakaian endpoint dengan config.py serta kode model.

## Setup lokal

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Isi konfigurasi database dan rahasia untuk lingkungan lokal.
```

Pada database baru/kosong, urutan awal historis:

```bash
mysql -u root -p nama_database < database/schema.sql
mysql -u root -p nama_database < database/schema_fase1.sql
```

Sebelum menjalankan aplikasi, terapkan migrasi lanjutan yang memang diperlukan setelah meninjau berkas database dan models.py. Jangan mengimpor ulang SQL inisialisasi ke database produksi berisi data, dan jangan menganggap db.create_all memperbarui tabel lama.

```bash
python app.py
```

Seed admin hanya untuk bootstrap terkendali. Jangan aktifkan SEED_ENABLED di produksi normal, dan jangan memakai kredensial bawaan.

## Deployment shared hosting

Baca [panduan Fase 1](docs/panduan_deployment_fase1.md), skrip deploy, dan [catatan terkini](docs/CATATAN-PROGRES.md) bersama-sama.

- Backend: jalankan deploy-production.sh --dry-run sebelum --apply; gunakan PIJAR_EXPECTED_COMMIT untuk mengikat commit yang dipasang.
- Frontend: git pull mengubah berkas repo, bukan otomatis semua salinan di document root. Periksa symlink atau jalankan penyalinan yang sesuai.
- Contoh jalur halaman pengguna pada server sesi ini: pengguna.html -> frontend/admin/pengguna.html. Verifikasi target dan berkas yang sudah ada sebelum membuat symlink; jangan menimpa tanpa pemeriksaan.
- Periksa juga js/sidebar.js dan login.html yang benar-benar dilayani. Menu relatif pengguna.html harus menuju halaman pada lokasi frontend yang sama.
- Pemanggilan sidebar.js di HTML belum diperbarui versi cache-nya pada PR #27/#28; hard reload untuk uji dan rencanakan cache busting.
- Jangan mengekspos repo, .git, .env, kode backend, atau dump database melalui document root. Status pemeriksaan paparan server belum terkonfirmasi.

## Pengujian dan batasan

- Uji teknisi produksi: login 200, template impor 403, tanpa token 401, dan mutasi aset 201; 4/4 lulus.
- PR #26/#27/#28: browser, integration, production-schema 10.6 dan 10.11 lulus.
- Tangkapan layar membuktikan daftar pengguna/regu/status tampil; belum membuktikan seluruh aksi dan seluruh ukuran layar.
- Belum ada tes browser khusus baru yang mencakup semua fitur pengguna/sidebar/identitas. CI hijau tidak sama dengan validasi visual lengkap.
- Pengujian yang menulis data produksi memerlukan persetujuan, akun/data uji, dan rencana pembersihan.

Pekerjaan lanjutan: penanganan hash rusak (login pernah 500), JSON/CORS error global, evaluasi pool koneksi, rate limiting login, blacklist lintas proses, logout server/revokasi sesi, keamanan document root, dan tes browser khusus. Lihat catatan progres untuk status detail.

## Di luar scope saat ini

- Prediksi kerusakan/preventive maintenance lanjutan (Fuzzy-PID).
- Mode offline penuh dan sinkronisasi lokal.
- Portal pelaporan warga publik.
- CSV bulk import (ditunda).

## Rujukan regulasi proyek

Daftar ini dipertahankan dari dokumentasi awal. Pembaruan README ini tidak memverifikasi ulang isi pasal atau interpretasi teknisnya; gunakan naskah resmi untuk keputusan kepatuhan.

| Regulasi | Konteks rujukan awal |
|---|---|
| Pergub DIY No. 25 Tahun 2019 | Terminologi kemantren/kalurahan dan referensi kode wilayah |
| Perda Kota Yogyakarta No. 4 Tahun 2020 | Pembentukan kemantren |
| Perwal Kota Yogyakarta No. 37 Tahun 2023 | Tugas/fungsi DPUPKP dan UPT PJU |
| Perwal Kota Yogyakarta No. 50 Tahun 2022 | Referensi kategori/spesifikasi penerangan |

## Lisensi dan kerahasiaan

Repository privat, berkaitan dengan infrastruktur pemerintah. Privat bukan berarti berkas server otomatis terlindungi. Jangan commit kredensial database, password, token, hash lengkap, atau dump produksi. Gunakan .env berdasarkan .env.example dan periksa aturan pengabaian serta akses web. Belum ada lisensi publik yang dinyatakan di README ini.

---
<p align="center">&copy; 2026 UPT Penerangan Jalan Umum &middot; Dinas PUPKP Kota Yogyakarta</p>

Tahun footer README adalah tahun pembaruan dokumen; tahun footer aplikasi dihitung otomatis di browser.
