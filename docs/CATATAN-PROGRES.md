# Catatan Progres PIJAR (PJU Kota Yogyakarta)

PIJAR: PENGUATAN INVENTARISASI JARINGAN ASET YANG RESPONSIF.

Terakhir diperbarui: 8 Oktober 2026, 19:32 WIB.
Acuan rilis bulk import: main setelah PR #30, merge commit 8042a3f6d2fc8091b965bec72354872cc36c60aa.

## Pembaruan terkini: PR #29 dan #30

- PR #29 telah merged: README dan catatan progres diselaraskan sampai perkembangan PR #28. Panduan deployment Fase 1 belum diperbarui.
- PR #30 telah merged ke main pada 8 Oktober 2026, 18:36:51 WIB. Commit implementasi awal 18332b291d41459e910340f20626906aa960629a; perbaikan header/penemuan tes 83134688d27b64f7ddc445027b5aa6f4e2412622; merge commit 8042a3f6d2fc8091b965bec72354872cc36c60aa.
- Nomor urut manual 1-9999 didukung pada kolom nomor_urut. Sistem menyusun kode kategori-wilayah-tahun-nomor empat digit, contoh PJUP-PA1-26-0001. Input 1/001/0001 menghasilkan nomor 0001; nol, negatif, pecahan dan lebih dari 9999 ditolak.
- Isi kode_aset lengkap ATAU nomor_urut + kode_kategori + kode_wilayah + tahun_pemasangan. Jika kode dan komponen diisi bersama, harus sesuai. Tahun wajib untuk penyusunan kode; kode lengkap lama tetap mengikuti aturan tahun opsional yang ada.
- Kontrak ASSET/LAMP lama dipertahankan. Template baru memakai ASSET_V2/LAMP_V2; parser menerima kedua versi. Kode lengkap tiga digit lama tidak diganti otomatis. Nomor saja pada kolom kode_aset tetap ditolak; pindahkan ke nomor_urut pada template baru dan kosongkan kode_aset.
- Sheet lampu dapat memakai kode lengkap atau komponen penyusunan yang sama; nomor_urut saja tidak cukup. Relasi diselesaikan terhadap kode akhir aset dalam batch. Data_Lampu wajib tersedia, boleh kosong.
- Alias sektor angka 1-4 dipetakan ke Sektor 1-4; KOTA dipetakan ke Jalan Kota. Wilayah tidak ditebak dari alamat. Alamat tetap wajib.
- Pencarian duplikat dilakukan setelah normalisasi, mencakup padanan tiga/empat digit; duplikat dalam batch diperiksa berdasarkan identitas kategori/wilayah/tahun/nomor. Tidak menimpa data existing.
- Batas route dan layanan disamakan menjadi 4 MB; maksimum 1000 baris aset+lampu. Formula tetap dilarang. Template tetap dikirim sebagai Response berisi byte untuk LiteSpeed.

### Hasil CI dan rollback PR #30

- Run awal integration: 61 tes, failures=3 dan errors=19. Kegagalan berulang nomor_urut terjadi setelah konstanta header diubah; fixture berurutan lama tidak kompatibel. Tes HTTP menerima 400 pada pratinjau; test_rollback berhenti di validate sebelum persist. Ini bukan bukti kerusakan rollback database.
- Perbaikan: ASSET/LAMP kembali ke header lama, header V2 dipisahkan, pembuat template memakai V2, dan tes dipindahkan ke tests/test_aset_bulk_four_digit.py. Ada 15 metode tes empat digit termasuk regresi header positional lama.
- Seluruh check commit 83134688d27b64f7ddc445027b5aa6f4e2412622 lulus: integration, browser, production-schema MariaDB 10.6/10.11, dan syntax-check. Enam hasil check tercatat karena syntax-check berjalan pada push dan PR. Ini hasil commit PR, bukan klaim run pasca-merge atau uji production.
- Log integration yang diberikan pengguna: Ran 76 tests in 16.375s, OK; 15 tes empat digit, test_commit, test_koordinator_preview, test_akun_nonaktif_ditolak, test_save_relations dan test_rollback semuanya ok, tidak skipped.
- Kode test_rollback memakai listener Lampu.before_insert yang melempar RuntimeError. persist melakukan flush aset terlebih dahulu; kegagalan lampu memicu rollback. Assertion memastikan jumlah aset=0 dan lampu=0 pada database uji yang awalnya kosong.
- Kelas MariaDBTests hanya opt-in saat PIJAR_DISPOSABLE_DB=yes dan menolak nama database selain pijar_bulk_test. setUp/tearDown memakai drop_all; JANGAN jalankan terhadap database operasional.
- Belum diuji oleh test_rollback tersebut: pelestarian aset/lampu lama, kegagalan setelah sebagian lampu tersimpan, dan injeksi kegagalan melalui endpoint HTTP commit.

### Status deployment dan data nyata

- Instruksi deploy telah diberikan: backup database, periksa perubahan lokal, update main, verifikasi commit rilis, set PIJAR_EXPECTED_COMMIT, jalankan --dry-run sebelum --apply.
- Belum ada laporan hasil --dry-run/--apply, verifikasi template live baru, atau simpan batch production sesudah PR #30. Status aktif di server BELUM DIKONFIRMASI; merge tidak sama dengan deploy.
- Setelah backend baru aktif, unduh ulang template XLSX dan salin berdasarkan nama kolom. Mulai pratinjau 2-5 baris tanpa simpan.
- Workbook yang dianalisis berisi 501 aset. Setelah nomor dipindahkan ke nomor_urut dalam memori, 500 baris lolos validasi terpisah memakai master contoh; baris Excel 9 ditolak karena alamat kosong. Bukan verifikasi duplikat database live atau batas wilayah.
- Verifikasi kode wilayah terhadap lokasi sebenarnya sebelum membakukan kode; alamat workbook mengandung nama wilayah yang tidak selalu cocok dengan kode. Jangan memperbaiki wilayah/alamat otomatis hanya untuk lolos validasi.

### Batasan rilis yang tetap terbuka

- Perlindungan duplikat identitas padanan tiga/empat digit pada permintaan bersamaan/lintas endpoint belum menyeluruh; UNIQUE string tidak cukup. Pemeriksaan existing saat preview/commit tidak menghilangkan race condition.
- Jalur tambah/cek/saran kode manual belum seluruhnya diselaraskan dengan format empat digit dan pemeriksaan identitas padanan. Saran berbasis urutan teks pada suffix campuran perlu ditinjau.
- Merge PR #30 disetujui dengan batasan tersebut. CI hijau dan merge tidak berarti semua release gates selesai. Lihat docs/BULK-IMPORT-4-DIGIT-RELEASE-GATES.md; bagian bukti CI/HTTP/rollback di atas memperbarui status pengujian, sementara batasan lain tetap berlaku.
- Tidak ada migrasi database baru pada patch PR #30. Jangan mengimpor ulang SQL inisialisasi untuk deployment ini.

## Selesai

### Aset dan bulk import

- Bulk Import aset dan lampu: template Excel, pratinjau, simpan atomik, penolakan kode duplikat tanpa menimpa. Versi sebelum PR #30 terverifikasi di produksi: pratinjau, simpan, duplikat ditolak, hapus aset uji. Verifikasi production format empat digit belum dikonfirmasi.
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
9. Komentar Blueprint usang di aset_bulk_routes.py sudah dihapus pada PR #30. Periksa ulang dugaan typo return1 pada deploy-production.sh dan pesan CSV yang menimpa status Berkas valid; belum dikonfirmasi masih ada di main terbaru.
10. README sudah diselaraskan sampai PR #28 melalui PR #29; selaraskan lagi untuk format empat digit dan perbarui panduan deployment Fase 1. Commit catatan ini tidak mengubah kedua berkas tersebut.
11. Selesaikan perlindungan duplikat identitas padanan lintas permintaan dan konsistensi jalur tambah/cek/saran kode manual sebelum memperluas impor production.
12. Tambahkan tes rollback dengan data lama, kegagalan setelah sebagian lampu masuk, dan kegagalan transaksi melalui HTTP commit.
13. Konfirmasikan deploy PR #30, verifikasi template live, perbaiki alamat baris Excel 9, verifikasi wilayah, lalu pratinjau batch kecil sebelum simpan.

## Batasan keamanan yang masih berlaku

- Seed admin harus tetap disabled di produksi (SEED_ENABLED tidak aktif). Nilai bawaan GANTI_INI dan pijar2026 tidak boleh dipakai sebagai kredensial produksi.
- Pembatasan menu di browser bukan kontrol keamanan. API tetap wajib memeriksa token, status akun, dan peran dari database.
- Jangan menyimpan password/token/hash lengkap dalam dokumentasi, log uji, screenshot, atau commit.
