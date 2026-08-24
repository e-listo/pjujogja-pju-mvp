# Panduan Deployment PIJAR — Fase 1 (Infrastruktur & Data)

## 1. Setup Subdomain di cPanel
Buat 3 subdomain melalui **cPanel > Domains > Subdomains**:

| Subdomain | Fungsi | Document Root |
|---|---|---|
| `admin.pjujogja.id` | Dashboard admin PIJAR (peta + task list + login) | `~/admin.pjujogja.id` |
| `api.pjujogja.id` | Backend REST API (Flask via Passenger) | `~/pjujogja_api` (di luar public_html) |
| `pins.pjujogja.id` | Antarmuka/API inventaris PINS (fase lanjutan) | `~/public_html/pins` |

> **Penting:** Document root `admin.pjujogja.id` berada di `~/admin.pjujogja.id/`, **bukan** di dalam `public_html/`. Sesuaikan path saat `git pull` atau upload file.

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
4. Upload `app.py`, `auth_routes.py`, `passenger_wsgi.py`, `config.py`, `models.py`, lalu **Restart**.

## 3. Setup Database MariaDB
1. Buat database `pjujogja_db` dan user privilege ALL via **cPanel > MySQL Databases**.
2. Import `database/schema.sql` via phpMyAdmin.
3. Verifikasi tabel: `pengguna`, `aset_pju`, `stok_pins`, `laporan_kerja`.
4. Import `database/schema_fase1.sql` (jalankan **setelah** `schema.sql`).

## 4. Deploy Frontend ke Server

```bash
# SSH ke server, lalu:
cd ~/admin.pjujogja.id
git pull origin main
```

Struktur file yang aktif di `~/admin.pjujogja.id/`:

| File | Keterangan |
|---|---|
| `login.html` | Halaman login PIJAR (entry point) |
| `index.html` | Dashboard admin (peta + task list) |
| `lapangan/lapor.html` | Form lapor kerusakan baru |
| `lapangan/form.html` | Form update status selesai perbaikan + potong stok PINS |

## 5. Verifikasi Milestone Fase 1
- `GET https://api.pjujogja.id/api/health` mengembalikan JSON sukses dengan HTTPS valid.
- Uji CRUD dasar `POST/GET /api/aset`.
- Login via `https://admin.pjujogja.id/login.html` berhasil dan redirect ke `index.html`.
- `pool_recycle=280` mengatasi isu "MySQL server has gone away" pada shared hosting.

---

## Roadmap Ringkas Fase 2–4

**Fase 2 (Backend API)** — lihat `app.py` & `auth_routes.py`: endpoint aset, laporan, autentikasi JWT, potong stok PINS atomik, target respons <500ms.

**Fase 3 (Frontend)** — semua file frontend di-deploy via `git pull` ke `~/admin.pjujogja.id/`. Uji tampilan di layar tablet 8" via DevTools sebelum uji fisik perangkat (Xiaomi Tab 8 Pro).

**Fase 4 (UAT)** — checklist sign-off:
- [ ] Admin berhasil login dan melihat dashboard peta.
- [ ] Admin berhasil input laporan & melihat prioritas otomatis.
- [ ] Regu lapangan submit `lapor.html` dari smartphone/tablet, foto terunggah <5 detik.
- [ ] Regu lapangan tandai selesai via `form.html`, stok PINS berkurang tepat sesuai qty.
- [ ] Bahasa antarmuka & ukuran tombol mudah dipahami pengguna non-teknis.
- [ ] Tidak ada bug kritis selama simulasi end-to-end.
