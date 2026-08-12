from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Kategori jalan resmi sesuai Perwal Kota Yogyakarta No. 50/2022 Pasal 33,
# ditambah "Lainnya" untuk penerangan non-jalan (Pasal 1 & 13).
KATEGORI_JALAN = ("Jalan Kota", "Jalan Lingkungan", "Jalan Lingkungan Kampung", "Lainnya")
SUB_KATEGORI_LAINNYA = ("Taman", "Makam", "Sorot Sungai", "Hias/Budaya")


class Pengguna(db.Model):
    __tablename__ = "pengguna"
    id_pengguna = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    peran = db.Column(db.Enum("admin", "teknisi"), default="teknisi")
    status_aktif = db.Column(db.Boolean, default=True)


class AsetPJU(db.Model):
    __tablename__ = "aset_pju"
    id_aset = db.Column(db.Integer, primary_key=True)
    kode_aset = db.Column(db.String(30), unique=True, nullable=False)
    alamat = db.Column(db.String(255), nullable=False)
    lokasi_lat = db.Column(db.Numeric(10, 8), nullable=False)
    lokasi_lng = db.Column(db.Numeric(11, 8), nullable=False)
    kategori_jalan = db.Column(db.Enum(*KATEGORI_JALAN), default="Jalan Lingkungan")
    sub_kategori_lainnya = db.Column(db.Enum(*SUB_KATEGORI_LAINNYA), nullable=True)
    jenis_lampu = db.Column(db.String(50))
    watt = db.Column(db.SmallInteger)
    status = db.Column(
        db.Enum("Menyala", "Rusak", "Dalam Pengerjaan"), default="Menyala"
    )
    tanggal_pasang = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    laporan = db.relationship("LaporanKerja", backref="aset", lazy=True)

    def to_dict(self):
        return {
            "id_aset": self.id_aset,
            "kode_aset": self.kode_aset,
            "alamat": self.alamat,
            "lat": float(self.lokasi_lat),
            "lng": float(self.lokasi_lng),
            "kategori_jalan": self.kategori_jalan,
            "sub_kategori_lainnya": self.sub_kategori_lainnya,
            "jenis_lampu": self.jenis_lampu,
            "watt": self.watt,
            "status": self.status,
        }


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
        """
        Skor = bobot kategori (Perwal 50/2022) + bobot durasi mati.
        Kategori 'Lainnya' (taman/makam/sorot sungai/hias) diberi bobot
        setara Jalan Lingkungan Kampung karena tidak menyangkut
        keselamatan lalu lintas langsung.
        """
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
