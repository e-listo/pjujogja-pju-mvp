# Bulk import empat digit: batasan sebelum rilis

Status: patch untuk review/CI, belum siap deploy produksi.

- Sumber patch: aset_bulk_service.py dan aset_bulk_routes.py yang ditempel pengguna.
- 14 tes validasi lokal lulus. Belum menjalankan tes HTTP, MariaDB, rollback transaksi, atau production.
- Percobaan workbook: nomor kode dipindahkan ke nomor_urut hanya dalam memori. 500 baris lolos validasi terpisah memakai master contoh; baris Excel 9 ditolak karena alamat kosong. Ini bukan pemeriksaan duplikat live atau geografis.
- Sebelum rilis, periksa kode model, endpoint tambah/cek/saran kode, frontend, serta tes lama. Jalur manual perlu aturan empat digit dan pemeriksaan identitas padanan yang sama.
- String UNIQUE tidak mencegah dua kode padanan tiga/empat digit yang masuk bersamaan. Selesaikan perlindungan lintas permintaan/lintas endpoint sebelum menyatakan transisi aman.
- Jalankan tes HTTP preview/commit, kompatibilitas template lama/baru, lampu, konflik, serta rollback MariaDB; pastikan CI lulus.
- Kode lengkap lama tiga digit dipertahankan; kode yang disusun dari nomor memakai empat digit. Tidak mengubah data lama otomatis.
- Formula ditolak; alamat wajib; wilayah tidak ditebak. Batas berkas 4 MB, 1000 baris total. Pemisah CSV titik koma belum didukung.
- Merge dan deployment memerlukan persetujuan terpisah. Jangan mengimpor data produksi sebelum pratinjau bersih dan pemeriksaan data selesai.
