# Panduan Deployment MVP PJU Jogja — Fase 1 (Infrastruktur & Data)

## 1. Setup Subdomain di cPanel
Buat 3 subdomain melalui **cPanel > Domains > Subdomains**:

| Subdomain | Fungsi | Document Root |
|---|---|---|
| `admin.pjujogja.id` | Dashboard admin (peta + task list) | `public_html/admin` |
| `api.pjujogja.id` | Backend REST API (Flask via Passenger) | `pjujogja_api` (di luar public_html) |
| `pins.pjujogja.id` | Antarmuka/API inventaris PINS (fase lanjutan) | `public_html/pins` |

Aktifkan **AutoSSL** untuk ketiga subdomain via **cPanel > Security > SSL/TLS Status**.

## 2. Setup Python App (untuk api.pjujogja.id)
1. **cPanel > Software > Setup Python App > Create Application**:
   - Python version: 3.10/3.11
   - Application root: `pjujogja_api`
   - Application URL: `api.pjujogja.id`
   - Startup file: `passenger_wsgi.py`
   - Entry point: `application`
2. Jalankan via Terminal cPanel:
   ```bash
   source /home/USER/virtualenv/pjujogja_api/3.x/bin/activate
   cd ~/pjujogja_api
   pip install -r requirements.txt
   ```
3. Tambahkan Environment Variables: `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME`, `SECRET_KEY`.
4. Upload `app.py`, `passenger_wsgi.py`, `config.py`, `models.py`, lalu **Restart**.

## 3. Setup Database MariaDB
1. Buat database `pjujogja_db` dan user privilege ALL via **cPanel > MySQL Databases**.
2. Import `database/schema.sql` via phpMyAdmin.
3. Verifikasi tabel: `pengguna`, `aset_pju`, `stok_pins`, `laporan_kerja`.

## 4. Verifikasi Milestone Fase 1
- `GET https://api.pjujogja.id/api/health` mengembalikan JSON sukses dengan HTTPS valid.
- Uji CRUD dasar `POST/GET /api/aset`.
- `pool_recycle=280` mengatasi isu "MySQL server has gone away" pada shared hosting.

---

## Roadmap Ringkas Fase 2–4

**Fase 2 (Backend API)** — lihat `app.py`: endpoint aset, laporan, potong stok PINS atomik, target respons <500ms.

**Fase 3 (Frontend)** — upload `frontend/admin/index.html` ke `public_html/admin/index.html` dan `frontend/lapangan/form.html` ke subfolder lapangan; uji tampilan di layar tablet 8" via DevTools sebelum uji fisik.

**Fase 4 (UAT)** — checklist sign-off:
- [ ] Admin berhasil input laporan & melihat prioritas otomatis.
- [ ] Regu lapangan submit form dari smartphone/tablet, foto <300KB terunggah <5 detik.
- [ ] Stok PINS berkurang tepat sesuai qty setelah tiket Selesai dengan penggantian komponen.
- [ ] Bahasa antarmuka & ukuran tombol mudah dipahami pengguna non-teknis.
- [ ] Tidak ada bug kritis selama simulasi end-to-end.
