# Catatan Progres PIJAR (PJU Kota Yogyakarta)

PIJAR: PENGUATAN INVENTARISASI JARINGAN ASET YANG RESPONSIF.

Terakhir diperbarui: 8 Oktober 2026, 17:17 WIB.
Acuan kode: main setelah PR #28, commit a257ef7e40bc2ea2f3158bd2a1006918bcbed188.

## Selesai

### Aset dan bulk import

- Bulk Import aset dan lampu: template Excel, pratinjau, simpan atomik, penolakan kode duplikat tanpa menimpa. Terverifikasi di produksi: pratinjau, simpan, duplikat ditolak, hapus aset uji.
- Popup Bulk Import diseragamkan dengan modal aset (PR #17).
- Unduh template di LiteSpeed memakai Response berisi byte, bukan send_file(BytesIO) (PR #18).
- Pesan error angka spesifik per kolom, misalnya lat harus antara -90 dan 90 (PR #19).
- Template CSV dinonaktifkan sementara (PR #20).
- Fixture Excel untuk tes HTTP dibuat sekali per tes agar preview dan commit memakai byte/hash yang sama (PR #25). Run CI sesudah perbaikan lulus; satu run tidak membuktikan seluruh sumber flakiness telah hilang.

### Autentikasi dan manajemen pengguna

- Backend manajemen pengguna (PR #22 dan #23): daftar dengan pencarian/filter/paginasi, tambah, detail, ubah profil/peran/regu/no. HP/status, reset password oleh admin, serta ganti password sendiri.
- Tidak ada hapus pengguna; nonaktifkan akun untuk mempertahankan relasi dan riwayat.
- Admin tidak boleh menonaktifkan atau mengganti peran akunnya sendiri. Regu boleh kosong dan dapat diganti; validasi backend menolak regu tidak aktif.
- Password dibuat dengan hash Werkzeug. Admin menentukan password saat membuat/reset akun; belum ada penanda wajib ganti password.
- jwt_required memuat akun dari database pada setiap permintaan: akun nonaktif/tidak ditemukan ditolak 401, dan peran terbaru dipakai tanpa menunggu token baru.
- Audit buat/ubah/reset/ganti password dicatat pada log aplikasi; contoh buat dan ubah akun telah terlihat di stderr.log produksi. Log bukan tabel audit permanen.
- Alias role_required('regu') dipetakan ke peran teknisi (PR #25). Regu adalah kelompok kerja, bukan nilai enum akun; peran akun tetap admin, koordinator, teknisi.
- Frontend pengguna.html (PR #26): daftar, cari/filter/paginasi, tambah/ubah, reset password, aktif/nonaktif, dan tampilan responsif. Data daftar dirender dengan textContent.

### Sidebar dan identitas

- PR #27: menu Pengguna khusus admin di desktop dan drawer Lainnya, kotak akun navy-oranye, tombol Keluar, dukungan Escape/Tab dan pengelolaan fokus drawer. CSS komponen akun dibatasi ke sidebar/drawer.
- PR #28: kepanjangan PIJAR disamakan pada login dan header sidebar.
- Footer sidebar/drawer mengikuti teks login: © [tahun] UPT Penerangan Jalan Umum · Dinas PUPKP Kota Yogyakarta. Tahun otomatis; footer sidebar rata tengah dengan warna abu terang agar terbaca. Teks sama, warna dan pembungkusan menyesuaikan wadah.
- Logout frontend masih menghapus token lokal tanpa memanggil endpoint logout server. Pembatasan menu mengikuti token untuk tampilan saja; otorisasi tetap dilakukan backend.

### Deployment dan CI

- deploy-production.sh: preflight, --dry-run/--apply, PIJAR_EXPECTED_COMMIT (PR #15 dan #16).
- Workflow CI: browser (Playwright), integration, production-schema MariaDB 10.6/10.11, dan syntax-check sesuai pemicu workflow.
- PR #26, #27, dan #28 masing-masing memiliki empat check yang lulus: browser, integration, production-schema 10.6 dan 10.11. Tidak ada tes browser khusus baru untuk seluruh fitur pengguna/sidebar/identitas.

## Bukti pengujian dan batasannya

- Uji teknisi produksi 8 Oktober 2026: login 200; template impor ditolak 403; permintaan tanpa token ditolak 401; POST mutasi aset uji 201. Ringkasan 4/4 lulus. Ini membuktikan jalur mutasi teknisi melewati pemeriksaan izin; bukan uji lengkap seluruh endpoint lapangan.
- Login akun uji sempat 500 akibat ValueError: Invalid hash method ''. Setelah hash akun diperbaiki menggunakan Werkzeug, login kembali 200. Penanganan hash rusak di kode login belum diperbaiki.
- Tangkapan layar pengguna memperlihatkan daftar akun, peran, status, regu terisi, dan tombol nonaktifkan akun sendiri dinonaktifkan. Belum ada laporan uji lengkap seluruh aksi frontend/reset/paginasi.
- Pengguna melaporkan tampilan clean pada akhir sesi. Pemeriksaan visual seluruh ukuran layar dan alur login setelah PR #28 belum terdokumentasi sebagai tes khusus.
- Merge GitHub, git pull server, dan frontend yang benar-benar dilayani adalah tahap berbeda. Jangan menyatakan commit sudah aktif di produksi hanya karena PR sudah merged.

## Catatan teknis operasional

- LiteSpeed LSAPI pernah menghasilkan io.UnsupportedOperation: fileno pada send_file(BytesIO). Gunakan Response berisi byte untuk template.
- Frontend admin menggunakan https://api.pjujogja.id sebagai base API; login ada pada POST /api/auth/login. Menembak subdomain admin untuk endpoint tersebut pernah menghasilkan 404 HTML.
- Repo server berada di ~/admin.pjujogja.id. Sebelum penyesuaian symlink, /pengguna.html menjawab 404, /frontend/admin/pengguna.html menjawab 200, dan /aset.html menjawab 200.
- Frontend aktif setelah git pull jika jalur yang dilayani menunjuk ke berkas repo melalui symlink. Jika berupa salinan, jalankan alur deploy frontend yang sesuai. Periksa document root dan readlink; jangan menimpa berkas/symlink yang ada tanpa verifikasi.
- Symlink yang diusulkan untuk halaman pengguna: pengguna.html -> frontend/admin/pengguna.html. Periksa juga apakah js/sidebar.js menunjuk atau sama dengan frontend/admin/js/sidebar.js. Hasil pembuatan symlink belum dilampirkan dalam log sesi ini.
- Backend menggunakan deploy-production.sh --apply. Sebelum --apply, jalankan --dry-run dan set PIJAR_EXPECTED_COMMIT ke commit yang akan dipasang.
- Versi cache pemanggilan sidebar.js pada HTML belum diperbarui dalam PR #27/#28; hard reload dapat diperlukan saat uji, dan pembaruan versi harus direncanakan.
- Mutasi uji menghasilkan satu catatan permanen. Pembersihan belum dikonfirmasi. Identifikasi baris uji dengan ID/keterangan sebelum menghapus; jangan menghapus riwayat secara luas. Nonaktifkan akun uji setelah tidak diperlukan.
- PR #24 (dokumentasi manajemen pengguna) masih terbuka saat terakhir diperiksa. Pembaruan ini disusun dari main dan mencakup perkembangan sesudahnya; evaluasi penggantian/penutupan PR #24 terpisah, bukan merge otomatis.

## Ditunda

- Dukungan CSV. Excel berlokal Indonesia dapat menyimpan CSV dengan pemisah titik koma. Rencana: deteksi pemisah dari baris judul. Desimal koma sudah diterima pada layanan impor yang ada.

## Pekerjaan lanjutan

1. Tangani hash password rusak agar login tidak menghasilkan 500; respons generik dan log tanpa password/hash/token. Tambahkan tes regresi.
2. Penanganan error global agar respons 500 membawa JSON dan header CORS yang tepat, tanpa membocorkan traceback atau rahasia.
3. Periksa konfigurasi engine sebelum menambah pool_pre_ping/pool_recycle untuk MySQL server has gone away. Nilai recycle harus disesuaikan dengan timeout hosting; penyebab dan konfigurasi aktif belum diverifikasi.
4. Verifikasi paparan .git/config, .env, kode backend, dan dump database pada document root. Hasil pemeriksaan keamanan yang diminta belum diberikan; belum dapat dinyatakan aman atau bocor.
5. Tambahkan pembatasan percobaan login serta evaluasi blacklist logout lintas proses. Blacklist sekarang di memori proses, hilang saat restart dan tidak dibagi antar worker.
6. Hubungkan logout frontend dengan endpoint server dan evaluasi kebijakan sesi setelah reset password; belum ada revokasi seluruh sesi yang terdokumentasi.
7. Uji browser khusus pengguna/sidebar: admin/teknisi, tambah/ubah/reset/status, pencarian/paginasi, desktop/tablet/mobile, fokus drawer, pembungkusan identitas/footer, dan cache aset.
8. Uji simpan dengan lampu di produksi memakai data asli kecil setelah persetujuan. Aset yang punya lampu tidak bisa dihapus lewat aplikasi; siapkan strategi pembersihan sebelum uji.
9. Periksa ulang pembersihan lama: komentar usang aset_bulk_routes.py, dugaan typo return1 pada deploy-production.sh, dan pesan CSV yang menimpa status Berkas valid. Belum dikonfirmasi masih ada di main terbaru.
10. Selaraskan README dan panduan deployment setelah isi berkas lama ditinjau; pembaruan catatan ini tidak otomatis mengubah kedua berkas tersebut.

## Batasan keamanan yang masih berlaku

- Seed admin harus tetap disabled di produksi (SEED_ENABLED tidak aktif). Nilai bawaan GANTI_INI dan pijar2026 tidak boleh dipakai sebagai kredensial produksi.
- Pembatasan menu di browser bukan kontrol keamanan. API tetap wajib memeriksa token, status akun, dan peran dari database.
- Jangan menyimpan password/token/hash lengkap dalam dokumentasi, log uji, screenshot, atau commit.
