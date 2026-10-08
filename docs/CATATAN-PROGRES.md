# Catatan Progres PIJAR (PJU Kota Yogyakarta)

Terakhir diperbarui: 8 Oktober 2026

## Selesai

- Bulk Import aset dan lampu: template Excel, pratinjau, simpan atomik, penolakan kode duplikat (tidak menimpa). Terverifikasi di produksi: pratinjau, simpan, duplikat ditolak, hapus aset uji.
- Popup Bulk Import diseragamkan dengan modal aset (PR #17).
- Perbaikan unduh template di LiteSpeed: pakai `Response` berisi byte, bukan `send_file(BytesIO)` (PR #18).
- Pesan error angka spesifik per kolom, misalnya "lat harus antara -90 dan 90" (PR #19).
- Template CSV dinonaktifkan sementara (PR #20).
- `deploy-production.sh`: preflight, `--dry-run`/`--apply`, `PIJAR_EXPECTED_COMMIT` (PR #15, #16).
- CI: browser (Playwright), integration, production-schema (MariaDB 10.6 dan 10.11), syntax-check.

## Ditunda

- Dukungan CSV. Excel berlokal Indonesia menyimpan CSV dengan pemisah titik koma. Rencana: deteksi pemisah dari baris judul. Desimal koma sudah diterima.

## Direncanakan

1. Manajemen user (berikutnya, lihat bagian temuan di bawah).
2. Penanganan error global agar respons 500 membawa header CORS dan JSON.
3. `pool_pre_ping` dan `pool_recycle` untuk error `MySQL server has gone away` di `stderr.log`.
4. Uji simpan dengan lampu di produksi memakai data asli kecil. Aset yang punya lampu tidak bisa dihapus lewat aplikasi.
5. Pembersihan kecil: komentar usang di `aset_bulk_routes.py`, typo `return1` di `deploy-production.sh`, pesan CSV yang menimpa kotak status "Berkas valid".

## Temuan audit auth_routes.py (bahan manajemen user)

Endpoint yang ada: `login`, `logout`, `me`, `seed`. Belum ada CRUD pengguna, ganti kata sandi, maupun reset.

- `jwt_required` tidak memeriksa `status_aktif` di database. Akun yang dinonaktifkan tetap bisa memakai token lama sampai kedaluwarsa (default 12 jam).
- Peran dibawa di dalam token. Perubahan peran baru berlaku setelah token berganti.
- Blacklist logout disimpan di memori proses. Hilang saat restart dan tidak dibagi antar proses.
- Belum ada pembatasan percobaan login.
- `Pengguna.peran` adalah enum `admin`, `koordinator`, `teknisi`. Tidak ada kolom `last_login`, `updated_at`, atau penanda wajib ganti kata sandi.
- `seed` punya nilai bawaan `GANTI_INI` dan `pijar2026`. Aman selama `SEED_ENABLED` tidak diaktifkan.

Usulan MVP: daftar pengguna (cari, saring peran dan status), tambah dan ubah (peran, regu), nonaktifkan alih-alih hapus, reset kata sandi oleh admin dengan kata sandi sementara, ganti kata sandi sendiri, catatan audit sederhana, pengecekan `status_aktif` di tiap permintaan, dan pembatasan percobaan login.

## Catatan teknis

- LiteSpeed LSAPI tidak cocok dengan `send_file(BytesIO)` (galat `io.UnsupportedOperation: fileno`). Gunakan `Response` berisi byte.
- Frontend aktif lewat `git pull`. Backend aktif lewat `deploy-production.sh --apply`.
- Sebelum `--apply`, jalankan `--dry-run` dan set `PIJAR_EXPECTED_COMMIT`.
