# Catatan Progres PIJAR (PJU Kota Yogyakarta)

Terakhir diperbarui: 8 Oktober 2026. Versi produksi api.pjujogja.id: `f061dcb` (PR #23).

## Selesai

### Bulk Import aset dan lampu

- Template Excel, pratinjau, simpan atomik, penolakan kode duplikat (tidak menimpa). Terverifikasi di produksi: pratinjau, simpan, duplikat ditolak, hapus aset uji.
- Popup Bulk Import diseragamkan dengan modal aset (PR #17).
- Perbaikan unduh template di LiteSpeed: pakai `Response` berisi byte, bukan `send_file(BytesIO)` (PR #18).
- Pesan error angka spesifik per kolom, misalnya "lat harus antara -90 dan 90" (PR #19).
- Template CSV dinonaktifkan sementara (PR #20).
- `deploy-production.sh`: preflight, `--dry-run`/`--apply`, `PIJAR_EXPECTED_COMMIT` (PR #15, #16).
- CI: browser (Playwright), integration, production-schema (MariaDB 10.6 dan 10.11), syntax-check.

### Manajemen pengguna, langkah 1 dan 2 (live di produksi sejak 8 Okt 2026)

- PR #22: `jwt_required` memeriksa database pada setiap permintaan. Akun dihapus atau nonaktif langsung ditolak 401. Peran, nama, dan username diambil dari database, bukan dari klaim token, sehingga perubahan peran langsung berlaku.
- PR #23: API pengguna khusus admin: `GET/POST /api/pengguna`, `GET/PUT/PATCH /api/pengguna/<id>`, `POST /api/pengguna/<id>/reset-password`. Semua pengguna login: `POST /api/auth/ubah-password`. Tidak ada `DELETE`.
- Uji produksi 8 langkah lulus: login admin, buat akun, login akun uji, akses admin ditolak 403 untuk teknisi, nonaktifkan akun, token lama 401, login ulang 401. Catatan `AUDIT pengguna` muncul di `stderr.log`.

## Keputusan desain manajemen pengguna

- Admin yang membuat akun dan mengetik password. Hanya admin yang boleh membuat dan mengubah akun (termasuk akun teknisi). Koordinator tidak.
- Regu boleh kosong dan bisa diganti kapan saja.
- Akun dinonaktifkan, tidak dihapus, karena punya relasi ke mutasi dan laporan.
- Admin tidak bisa menonaktifkan atau mengubah peran akunnya sendiri. Karena pelaku selalu admin aktif, aturan ini sekaligus menjamin selalu ada minimal satu admin aktif.
- Kode manajemen pengguna ada di `auth_routes.py`, bukan modul baru, karena `deploy-production.sh` menyalin daftar berkas backend yang tetap.

## Ditunda

- Dukungan CSV. Excel berlokal Indonesia menyimpan CSV dengan pemisah titik koma. Rencana: deteksi pemisah dari baris judul. Desimal koma sudah diterima.
- Pembatalan token lama setelah reset password. Perlu kolom baru (misalnya `password_diubah_pada`) dan migrasi.
- Pembatasan percobaan login (kunci sementara). Perlu penyimpanan di database, bukan memori, karena proses LiteSpeed bisa lebih dari satu.
- Blacklist logout masih di memori proses: hilang saat restart dan tidak dibagi antar proses.

## Direncanakan

1. Langkah 3 manajemen pengguna: halaman admin Manajemen Pengguna di frontend (modal seperti halaman Aset, ramah tablet): daftar, cari, saring, tambah, ubah, aktif/nonaktif, reset password, dan halaman ubah password sendiri.
2. Tinjau `role_required('regu', ...)` di `app.py` (mutasi aset, pemeliharaan). Peran `regu` tidak ada di `Pengguna.peran` (hanya `admin`, `koordinator`, `teknisi`), sehingga teknisi kemungkinan ditolak 403 di endpoint itu. Perlu diverifikasi di `app.py` repo sebelum dipakai di lapangan.
3. Penanganan error global agar respons 500 membawa header CORS dan JSON.
4. `pool_pre_ping` dan `pool_recycle` untuk error `MySQL server has gone away` di `stderr.log`.
5. Uji simpan dengan lampu di produksi memakai data asli kecil. Aset yang punya lampu tidak bisa dihapus lewat aplikasi.
6. Pembersihan kecil: komentar usang di `aset_bulk_routes.py`, pesan CSV yang menimpa kotak status "Berkas valid". Dugaan typo `return1` di `deploy-production.sh` ternyata artefak tempel terminal (`grep` kosong), dicabut dari daftar.

## Catatan teknis

- LiteSpeed LSAPI tidak cocok dengan `send_file(BytesIO)` (galat `io.UnsupportedOperation: fileno`). Gunakan `Response` berisi byte.
- Deploy backend: `git checkout main && git pull --ff-only`, lalu `bash deploy-production.sh --dry-run`, lalu `PIJAR_EXPECTED_COMMIT=<sha lengkap> bash deploy-production.sh --apply`. Berkas tidak punya hak eksekusi di server, jalankan dengan `bash`. Tunggu sekitar 20 detik agar aplikasi dimuat ulang. Perubahan hak akses `deploy.sh` (mode saja) diabaikan skrip.
- Daftar berkas backend yang disalin skrip deploy: `app.py`, `auth_routes.py`, `config.py`, `models.py`, `passenger_wsgi.py`, `aset_bulk_service.py`, `aset_bulk_routes.py`, `requirements.txt`. Berkas backend baru harus ditambahkan ke daftar itu di `deploy-production.sh`.
- Folder repositori di server (`~/admin.pjujogja.id`) juga folder web admin. Jangan menaruh skrip atau berkas uji di sana.
- CI menjalankan `unittest discover -p 'test_aset_bulk*.py'`. Nama berkas tes baru harus mengikuti pola itu, dan gayanya `unittest`, bukan pytest.
- Tes yang menghapus `Pengguna` lewat ORM di SQLite akan gagal karena relasi `mutasi` memuat tabel `mutasi_aset`. Hapus lewat SQL langsung.
- Frontend aktif lewat `git pull`. Backend aktif lewat skrip deploy.
