from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Konstanta kategori jalan — Perwal Kota Yogyakarta No. 50/2022 Pasal 33
# ditambah "Lainnya" untuk penerangan non-jalan (Pasal 1 & 13)
# ---------------------------------------------------------------------------
KATEGORI_JALAN = ("Jalan Kota", "Jalan Lingkungan", "Jalan Lingkungan Kampung", "Lainnya")
SUB_KATEGORI_LAINNYA = ("Taman", "Makam", "Sorot Sungai", "Hias/Budaya")


# ===========================================================================
# FASE 1 — Model yang sudah ada (tidak diubah, backward compatible)
# ===========================================================================

class StokPins(db.Model):
    __tablename__ = "stok_pins"
    id_komponen = db.Column(db.Integer, primary_key=True)
    nama_komponen = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(50))
    satuan = db.Column(db.String(20), default="pcs")
    stok_qty = db.Column(db.Integer, default=0)
    stok_minimum = db.Column(db.Integer, default=5)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_komponen": self.id_komponen,
            "nama_komponen": self.nama_komponen,
            "kategori": self.kategori,
            "satuan": self.satuan,
            "stok_qty": self.stok_qty,
            "stok_minimum": self.stok_minimum,
            "status_stok": "Menipis" if self.stok_qty <= self.stok_minimum else "Aman",
        }


# ===========================================================================
# FASE 2 — Model baru ERD PIJAR
# ===========================================================================

class Wilayah(db.Model):
    """
    45 kelurahan Kota Yogyakarta dalam 14 kemantren.
    kode_wilayah: CHAR(3) — 2 huruf prefix kemantren + 1 angka urut.
    Contoh: UH1 (Umbulharjo I/Giwangan), GK3 (Gondokusuman III/Kotabaru).
    Dasar: Pergub DIY No. 25/2019, Perda Kota Yogyakarta No. 4/2020.
    """
    __tablename__ = "wilayah"
    id_wilayah = db.Column(db.Integer, primary_key=True)
    kode_wilayah = db.Column(db.String(3), unique=True, nullable=False)
    nama_kemantren = db.Column(db.String(50), nullable=False)
    nama_kelurahan = db.Column(db.String(50), nullable=False)

    aset = db.relationship("AsetPJU", backref="wilayah", lazy="dynamic")
    panel = db.relationship("PanelPJU", backref="wilayah", lazy="dynamic")

    def to_dict(self):
        return {
            "id_wilayah": self.id_wilayah,
            "kode_wilayah": self.kode_wilayah,
            "nama_kemantren": self.nama_kemantren,
            "nama_kelurahan": self.nama_kelurahan,
        }


class PanelPJU(db.Model):
    """Gardu/panel distribusi listrik PJU per wilayah."""
    __tablename__ = "panel_pju"
    id_panel = db.Column(db.Integer, primary_key=True)
    id_wilayah = db.Column(db.Integer, db.ForeignKey("wilayah.id_wilayah"), nullable=False)
    kode_panel = db.Column(db.String(20), unique=True, nullable=False)
    kapasitas_kwh = db.Column(db.Numeric(8, 2))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    status = db.Column(db.Enum("Aktif", "Tidak Aktif", "Rusak"), default="Aktif")

    aset = db.relationship("AsetPJU", backref="panel", lazy="dynamic")

    def to_dict(self):
        return {
            "id_panel": self.id_panel,
            "id_wilayah": self.id_wilayah,
            "kode_panel": self.kode_panel,
            "kapasitas_kwh": float(self.kapasitas_kwh) if self.kapasitas_kwh else None,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "status": self.status,
        }


class Regu(db.Model):
    """4 regu pelaksana sesuai pembagian sektor UPT PJU Kota Yogyakarta."""
    __tablename__ = "regu"
    id_regu = db.Column(db.Integer, primary_key=True)
    nama_regu = db.Column(db.String(50), nullable=False)
    wilayah_tugas = db.Column(db.String(100))
    status_aktif = db.Column(db.Boolean, default=True)

    anggota = db.relationship("Pengguna", backref="regu", lazy="dynamic")
    pemeliharaan = db.relationship("RiwayatPemeliharaan", backref="regu", lazy="dynamic")

    def to_dict(self):
        return {
            "id_regu": self.id_regu,
            "nama_regu": self.nama_regu,
            "wilayah_tugas": self.wilayah_tugas,
            "status_aktif": self.status_aktif,
            "jumlah_anggota": self.anggota.count(),
        }


class Pengguna(db.Model):
    """
    Pengguna sistem — update Fase 2: tambah id_regu, no_hp, peran koordinator.
    """
    __tablename__ = "pengguna"
    id_pengguna = db.Column(db.Integer, primary_key=True)
    id_regu = db.Column(db.Integer, db.ForeignKey("regu.id_regu"), nullable=True)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    peran = db.Column(db.Enum("admin", "koordinator", "teknisi"), default="teknisi")
    no_hp = db.Column(db.String(20), nullable=True)
    status_aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_pengguna": self.id_pengguna,
            "id_regu": self.id_regu,
            "nama_lengkap": self.nama_lengkap,
            "username": self.username,
            "peran": self.peran,
            "no_hp": self.no_hp,
            "status_aktif": self.status_aktif,
        }


class AsetPJU(db.Model):
    """
    Aset tiang PJU — update Fase 2: tambah relasi wilayah, panel,
    jenis_tiang, tinggi_meter, foto_url.
    """
    __tablename__ = "aset_pju"
    id_aset = db.Column(db.Integer, primary_key=True)
    id_wilayah = db.Column(db.Integer, db.ForeignKey("wilayah.id_wilayah"), nullable=True)
    id_panel = db.Column(db.Integer, db.ForeignKey("panel_pju.id_panel"), nullable=True)
    kode_aset = db.Column(db.String(30), unique=True, nullable=False)
    alamat = db.Column(db.String(255), nullable=False)
    lokasi_lat = db.Column(db.Numeric(10, 8), nullable=False)
    lokasi_lng = db.Column(db.Numeric(11, 8), nullable=False)
    kategori_jalan = db.Column(db.Enum(*KATEGORI_JALAN), default="Jalan Lingkungan")
    sub_kategori_lainnya = db.Column(db.Enum(*SUB_KATEGORI_LAINNYA), nullable=True)
    jenis_tiang = db.Column(db.String(50), nullable=True)
    tinggi_meter = db.Column(db.Numeric(5, 2), nullable=True)
    jenis_lampu = db.Column(db.String(50))
    watt = db.Column(db.SmallInteger)
    status = db.Column(
        db.Enum("Menyala", "Rusak", "Dalam Pengerjaan"), default="Menyala"
    )
    foto_url = db.Column(db.String(255), nullable=True)
    tanggal_pasang = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    laporan = db.relationship("LaporanKerja", backref="aset", lazy=True)
    lampu = db.relationship("Lampu", backref="aset", lazy="dynamic")
    laporan_kerusakan = db.relationship("LaporanKerusakan", backref="aset", lazy="dynamic")
    riwayat_pemeliharaan = db.relationship("RiwayatPemeliharaan", backref="aset", lazy="dynamic")

    def to_dict(self):
        return {
            "id_aset": self.id_aset,
            "id_wilayah": self.id_wilayah,
            "id_panel": self.id_panel,
            "kode_aset": self.kode_aset,
            "alamat": self.alamat,
            "lat": float(self.lokasi_lat),
            "lng": float(self.lokasi_lng),
            "kategori_jalan": self.kategori_jalan,
            "sub_kategori_lainnya": self.sub_kategori_lainnya,
            "jenis_tiang": self.jenis_tiang,
            "tinggi_meter": float(self.tinggi_meter) if self.tinggi_meter else None,
            "jenis_lampu": self.jenis_lampu,
            "watt": self.watt,
            "status": self.status,
            "foto_url": self.foto_url,
        }


class Lampu(db.Model):
    """Komponen lampu per tiang — dipisah dari AsetPJU untuk mendukung multi-lampu per tiang."""
    __tablename__ = "lampu"
    id_lampu = db.Column(db.Integer, primary_key=True)
    id_aset = db.Column(db.Integer, db.ForeignKey("aset_pju.id_aset"), nullable=False)
    jenis_lampu = db.Column(db.String(50))
    daya_watt = db.Column(db.SmallInteger)
    merk = db.Column(db.String(50))
    tahun_pasang = db.Column(db.SmallInteger)
    status_lampu = db.Column(
        db.Enum("Menyala", "Mati", "Rusak", "Diganti"), default="Menyala"
    )

    def to_dict(self):
        return {
            "id_lampu": self.id_lampu,
            "id_aset": self.id_aset,
            "jenis_lampu": self.jenis_lampu,
            "daya_watt": self.daya_watt,
            "merk": self.merk,
            "tahun_pasang": self.tahun_pasang,
            "status_lampu": self.status_lampu,
        }


class LaporanKerusakan(db.Model):
    """
    Laporan kerusakan Fase 2 — lebih detail dari LaporanKerja.
    Mendukung sumber: Lapangan, JSS (Smart City), Masyarakat, Patroli.
    """
    __tablename__ = "laporan_kerusakan"
    id_laporan = db.Column(db.Integer, primary_key=True)
    id_aset = db.Column(db.Integer, db.ForeignKey("aset_pju.id_aset"), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey("pengguna.id_pengguna"), nullable=True)
    deskripsi_kerusakan = db.Column(db.Text, nullable=False)
    foto_url = db.Column(db.String(255))
    sumber_laporan = db.Column(
        db.Enum("Lapangan", "JSS", "Masyarakat", "Patroli"), default="Lapangan"
    )
    status_laporan = db.Column(
        db.Enum("Baru", "Diproses", "Selesai", "Ditolak"), default="Baru"
    )
    tanggal_lapor = db.Column(db.DateTime, default=datetime.utcnow)

    pelapor = db.relationship("Pengguna", foreign_keys=[id_user], lazy=True)
    pemeliharaan = db.relationship("RiwayatPemeliharaan", backref="laporan", lazy="dynamic")

    def to_dict(self):
        return {
            "id_laporan": self.id_laporan,
            "id_aset": self.id_aset,
            "kode_aset": self.aset.kode_aset if self.aset else None,
            "alamat": self.aset.alamat if self.aset else None,
            "lat": float(self.aset.lokasi_lat) if self.aset else None,
            "lng": float(self.aset.lokasi_lng) if self.aset else None,
            "deskripsi_kerusakan": self.deskripsi_kerusakan,
            "foto_url": self.foto_url,
            "sumber_laporan": self.sumber_laporan,
            "status_laporan": self.status_laporan,
            "tanggal_lapor": self.tanggal_lapor.isoformat(),
            "id_user": self.id_user,
        }


class RiwayatPemeliharaan(db.Model):
    """
    Log pekerjaan perbaikan/pemeliharaan oleh regu lapangan.
    Mendukung foto sebelum/sesudah sebagai bukti kerja.
    """
    __tablename__ = "riwayat_pemeliharaan"
    id_pemeliharaan = db.Column(db.Integer, primary_key=True)
    id_aset = db.Column(db.Integer, db.ForeignKey("aset_pju.id_aset"), nullable=False)
    id_regu = db.Column(db.Integer, db.ForeignKey("regu.id_regu"), nullable=True)
    id_user = db.Column(db.Integer, db.ForeignKey("pengguna.id_pengguna"), nullable=True)
    id_laporan = db.Column(db.Integer, db.ForeignKey("laporan_kerusakan.id_laporan"), nullable=True)
    jenis_pekerjaan = db.Column(db.String(100), nullable=False)
    deskripsi_pekerjaan = db.Column(db.Text)
    foto_sebelum = db.Column(db.String(255))
    foto_sesudah = db.Column(db.String(255))
    status_pekerjaan = db.Column(
        db.Enum("Dalam Pengerjaan", "Selesai", "Ditunda"), default="Dalam Pengerjaan"
    )
    tanggal_pengerjaan = db.Column(db.DateTime, default=datetime.utcnow)

    teknisi = db.relationship("Pengguna", foreign_keys=[id_user], lazy=True)

    def to_dict(self):
        return {
            "id_pemeliharaan": self.id_pemeliharaan,
            "id_aset": self.id_aset,
            "kode_aset": self.aset.kode_aset if self.aset else None,
            "id_regu": self.id_regu,
            "nama_regu": self.regu.nama_regu if self.regu else None,
            "id_user": self.id_user,
            "id_laporan": self.id_laporan,
            "jenis_pekerjaan": self.jenis_pekerjaan,
            "deskripsi_pekerjaan": self.deskripsi_pekerjaan,
            "foto_sebelum": self.foto_sebelum,
            "foto_sesudah": self.foto_sesudah,
            "status_pekerjaan": self.status_pekerjaan,
            "tanggal_pengerjaan": self.tanggal_pengerjaan.isoformat(),
        }


# ===========================================================================
# FASE 1 — LaporanKerja (dipertahankan sebagai arsip, tidak diubah)
# ===========================================================================

class LaporanKerja(db.Model):
    __tablename__ = "laporan_kerja"
    id_laporan = db.Column(db.Integer, primary_key=True)
    id_aset = db.Column(db.Integer, db.ForeignKey("aset_pju.id_aset"), nullable=False)
    id_teknisi = db.Column(db.Integer, db.ForeignKey("pengguna.id_pengguna"))
    tanggal_lapor = db.Column(db.DateTime, default=datetime.utcnow)
    tanggal_selesai = db.Column(db.DateTime)
    kategori_jalan_snap = db.Column(db.Enum(*KATEGORI_JALAN), nullable=False)
    sub_kategori_lainnya_snap = db.Column(db.Enum(*SUB_KATEGORI_LAINNYA), nullable=True)
    status = db.Column(db.Enum("Baru", "Dalam Pengerjaan", "Selesai"), default="Baru")
    tindakan_perbaikan = db.Column(db.String(100))
    id_komponen_pins = db.Column(db.Integer, db.ForeignKey("stok_pins.id_komponen"))
    qty_komponen = db.Column(db.Integer, default=1)
    foto_bukti = db.Column(db.String(255))
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    komponen = db.relationship("StokPins", lazy=True)

    def hitung_skor_prioritas(self, bobot_kategori: dict) -> int:
        bobot_jalan = bobot_kategori.get(self.kategori_jalan_snap, 1)
        durasi_jam = (datetime.utcnow() - self.tanggal_lapor).total_seconds() / 3600
        if durasi_jam < 6:
            bobot_durasi = 1
        elif durasi_jam < 24:
            bobot_durasi = 2
        elif durasi_jam < 72:
            bobot_durasi = 3
        else:
            bobot_durasi = 4
        return bobot_jalan + bobot_durasi

    def to_dict(self, bobot_kategori: dict):
        return {
            "id_laporan": self.id_laporan,
            "id_aset": self.id_aset,
            "kode_aset": self.aset.kode_aset if self.aset else None,
            "alamat": self.aset.alamat if self.aset else None,
            "lat": float(self.aset.lokasi_lat) if self.aset else None,
            "lng": float(self.aset.lokasi_lng) if self.aset else None,
            "tanggal_lapor": self.tanggal_lapor.isoformat(),
            "kategori_jalan": self.kategori_jalan_snap,
            "sub_kategori_lainnya": self.sub_kategori_lainnya_snap,
            "status": self.status,
            "skor_prioritas": self.hitung_skor_prioritas(bobot_kategori),
            "tindakan_perbaikan": self.tindakan_perbaikan,
            "foto_bukti": self.foto_bukti,
            "id_teknisi": self.id_teknisi,
        }
