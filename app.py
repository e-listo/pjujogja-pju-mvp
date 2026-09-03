"""
app.py — Entry point Flask untuk api.pjujogja.id
Fase 1: Model aset, laporan kerja, stok PINS.
Fase 2: Proteksi JWT, endpoint baru, pagination, atomisitas stok PINS.
Fase 3: Endpoint KategoriPJU, suggest-kode, cek-kode.
Fase 4: Endpoint mutasi aset, export aset, hapus aset.
"""
import os
import re
import uuid
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from models import (
    db,
    AsetPJU, LaporanKerja, StokPins, Pengguna, SUB_KATEGORI_LAINNYA,
    Wilayah, PanelPJU, Regu, Lampu, LaporanKerusakan, RiwayatPemeliharaan,
    KategoriPJU, MutasiAset,
)
from auth_routes import auth_bp, jwt_required, role_required

REGEX_KODE_ASET = re.compile(r'^[A-Z]{3,6}-[A-Z]{2}\d-\d{2}-\d{3}$')


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_upload(file_obj, upload_folder):
    ext = file_obj.filename.rsplit(".", 1)[1].lower()
    nama_file = f"{uuid.uuid4().hex}.{ext}"
    file_obj.save(os.path.join(upload_folder, secure_filename(nama_file)))
    return nama_file


def _paginate(query, default_per_page=20):
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", default_per_page, type=int)
    per_page = min(per_page, 100)
    items    = query.offset((page - 1) * per_page).limit(per_page + 1).all()
    has_next = len(items) > per_page
    items    = items[:per_page]
    if page == 1 and not has_next:
        total = len(items)
    else:
        total = query.count()
    return items, {
        "page":        page,
        "per_page":    per_page,
        "total":       total,
        "total_pages": max(1, (total + per_page - 1) // per_page),
        "has_next":    has_next,
    }


def _apply_aset_filters(query):
    status_filter = request.args.get("status")
    kategori_filter = request.args.get("kategori_jalan")
    id_wilayah_filter = request.args.get("id_wilayah", type=int)
    id_kategori_filter = request.args.get("id_kategori", type=int)
    kemantren_filter = request.args.get("kemantren")
    kelurahan_filter = request.args.get("kelurahan")
    kode_wilayah_filter = request.args.get("kode_wilayah")

    if status_filter:
        query = query.filter(AsetPJU.status == status_filter)
    else:
        query = query.filter(AsetPJU.status.in_(["Rusak", "Dalam Pengerjaan", "Menyala"]))
    if kategori_filter:
        query = query.filter(AsetPJU.kategori_jalan == kategori_filter)
    if id_wilayah_filter:
        query = query.filter(AsetPJU.id_wilayah == id_wilayah_filter)
    if id_kategori_filter:
        query = query.filter(AsetPJU.id_kategori == id_kategori_filter)
    if kemantren_filter:
        query = query.join(Wilayah, AsetPJU.id_wilayah == Wilayah.id_wilayah).filter(
            Wilayah.nama_kemantren.ilike(f"%{kemantren_filter}%")
        )
    if kelurahan_filter:
        query = query.join(Wilayah, AsetPJU.id_wilayah == Wilayah.id_wilayah).filter(
            Wilayah.nama_kelurahan.ilike(f"%{kelurahan_filter}%")
        )
    if kode_wilayah_filter:
        query = query.join(Wilayah, AsetPJU.id_wilayah == Wilayah.id_wilayah).filter(
            Wilayah.kode_wilayah.ilike(f"%{kode_wilayah_filter}%")
        )
    return query


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    app.register_blueprint(auth_bp)

    @app.route("/api/aset", methods=["GET"])
    @jwt_required
    def list_aset():
        q = _apply_aset_filters(AsetPJU.query)
        items, meta = _paginate(q.order_by(AsetPJU.id_aset.desc()))
        return jsonify({"success": True, "meta": meta, "data": [a.to_dict() for a in items]})

    @app.route("/api/aset/export", methods=["GET"])
    @jwt_required
    def export_aset():
        q = _apply_aset_filters(AsetPJU.query)
        items = q.order_by(AsetPJU.id_aset.desc()).all()
        return jsonify({
            "success": True,
            "total": len(items),
            "exported_at": datetime.utcnow().isoformat(),
            "data": [a.to_dict() for a in items]
        })

    @app.route("/api/aset/<int:id_aset>", methods=["GET"])
    @jwt_required
    def get_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        return jsonify({"success": True, "data": aset.to_dict()})

    @app.route("/api/aset", methods=["POST"])
    @role_required("koordinator", "admin")
    def create_aset():
        body = request.get_json(force=True)

        kode_aset = body.get("kode_aset", "").strip().upper()
        if not kode_aset:
            return jsonify({"success": False, "error": "kode_aset wajib diisi"}), 400
        if not REGEX_KODE_ASET.match(kode_aset):
            return jsonify({"success": False, "error": "Format kode_aset tidak valid. Gunakan: PJUP-UH2-26-001"}), 400
        if AsetPJU.query.filter_by(kode_aset=kode_aset).first():
            return jsonify({"success": False, "error": f"Kode aset '{kode_aset}' sudah dipakai"}), 409

        kategori_jalan = body.get("kategori_jalan", "Jalan Lingkungan")
        sub_kategori = body.get("sub_kategori_lainnya")
        if kategori_jalan == "Lainnya" and sub_kategori not in SUB_KATEGORI_LAINNYA:
            return jsonify({"success": False, "error": f"sub_kategori_lainnya wajib: {SUB_KATEGORI_LAINNYA}"}), 400
        if kategori_jalan != "Lainnya":
            sub_kategori = None

        try:
            aset = AsetPJU(
                kode_aset=kode_aset,
                id_kategori=body.get("id_kategori"),
                tahun_pemasangan=body.get("tahun_pemasangan"),
                alamat=body["alamat"],
                lokasi_lat=body["lat"],
                lokasi_lng=body["lng"],
                kategori_jalan=kategori_jalan,
                sub_kategori_lainnya=sub_kategori,
                id_wilayah=body.get("id_wilayah"),
                id_panel=body.get("id_panel"),
                jenis_tiang=body.get("jenis_tiang"),
                tinggi_meter=body.get("tinggi_meter"),
                jenis_lampu=body.get("jenis_lampu"),
                merk_lampu=body.get("merk_lampu"),
                tipe_lampu=body.get("tipe_lampu"),
                watt=body.get("watt"),
                status=body.get("status", "Menyala"),
            )
            db.session.add(aset)
            db.session.commit()
            return jsonify({"success": True, "data": aset.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/aset/<int:id_aset>", methods=["PUT"])
    @role_required("koordinator", "admin")
    def update_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        body = request.get_json(force=True)
        try:
            for field in [
                "alamat", "kategori_jalan", "sub_kategori_lainnya",
                "id_wilayah", "id_panel", "id_kategori",
                "jenis_tiang", "tinggi_meter", "jenis_lampu",
                "merk_lampu", "tipe_lampu", "watt",
                "status", "tahun_pemasangan", "foto_url",
            ]:
                if field in body:
                    setattr(aset, field, body[field])
            if "lat" in body:
                aset.lokasi_lat = body["lat"]
            if "lng" in body:
                aset.lokasi_lng = body["lng"]
            if aset.kategori_jalan == "Lainnya" and aset.sub_kategori_lainnya not in SUB_KATEGORI_LAINNYA:
                return jsonify({"success": False, "error": f"sub_kategori_lainnya wajib: {SUB_KATEGORI_LAINNYA}"}), 400
            if aset.kategori_jalan != "Lainnya":
                aset.sub_kategori_lainnya = None
            db.session.commit()
            return jsonify({"success": True, "data": aset.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/aset/<int:id_aset>", methods=["DELETE"])
    @role_required("koordinator", "admin")
    def delete_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        if aset.lampu.count() > 0 or aset.laporan_kerusakan.count() > 0 or aset.riwayat_pemeliharaan.count() > 0 or aset.mutasi.count() > 0:
            return jsonify({
                "success": False,
                "error": "Aset tidak bisa dihapus karena sudah punya relasi lampu/laporan/pemeliharaan/mutasi"
            }), 409
        try:
            db.session.delete(aset)
            db.session.commit()
            return jsonify({"success": True, "pesan": "Aset berhasil dihapus"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/aset/<int:id_aset>/mutasi", methods=["GET"])
    @jwt_required
    def list_mutasi_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        data = [m.to_dict() for m in aset.mutasi.order_by(MutasiAset.tanggal_mutasi.desc()).all()]
        return jsonify({
            "success": True,
            "aset": {"id_aset": aset.id_aset, "kode_aset": aset.kode_aset, "alamat": aset.alamat},
            "total": len(data),
            "data": data
        })

    @app.route("/api/aset/<int:id_aset>/mutasi", methods=["POST"])
    @role_required("regu", "koordinator", "admin")
    def create_mutasi_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404

        is_json = request.is_json
        body = request.get_json(force=True) if is_json else request.form
        foto = None if is_json else request.files.get("foto")
        foto_url = save_upload(foto, app.config["UPLOAD_FOLDER"]) if foto and allowed_file(foto.filename) else None

        jenis_mutasi = (body.get("jenis_mutasi") or "").strip()
        if not jenis_mutasi:
            return jsonify({"success": False, "error": "jenis_mutasi wajib diisi"}), 400

        try:
            mutasi = MutasiAset(
                id_aset=id_aset,
                id_petugas=body.get("id_petugas", type=int) if not is_json else body.get("id_petugas"),
                id_pemeliharaan=body.get("id_pemeliharaan", type=int) if not is_json else body.get("id_pemeliharaan"),
                jenis_mutasi=jenis_mutasi,
                status_sebelum=body.get("status_sebelum") or aset.status,
                status_sesudah=body.get("status_sesudah"),
                komponen=body.get("komponen"),
                qty=(body.get("qty", type=int) if not is_json else body.get("qty", 1)) or 1,
                lat_baru=body.get("lat_baru", type=float) if not is_json else body.get("lat_baru"),
                lng_baru=body.get("lng_baru", type=float) if not is_json else body.get("lng_baru"),
                alamat_baru=body.get("alamat_baru"),
                keterangan=body.get("keterangan"),
                foto_url=foto_url or body.get("foto_url"),
            )
            if body.get("tanggal_mutasi"):
                raw_tanggal = body.get("tanggal_mutasi")
                mutasi.tanggal_mutasi = datetime.fromisoformat(str(raw_tanggal).replace("Z", "+00:00"))

            db.session.add(mutasi)

            if mutasi.status_sesudah:
                aset.status = mutasi.status_sesudah
            if mutasi.jenis_mutasi == "Pindah Lokasi":
                if mutasi.alamat_baru:
                    aset.alamat = mutasi.alamat_baru
                if mutasi.lat_baru is not None:
                    aset.lokasi_lat = mutasi.lat_baru
                if mutasi.lng_baru is not None:
                    aset.lokasi_lng = mutasi.lng_baru
            if mutasi.jenis_mutasi == "Pensiun / Bongkar" and not mutasi.status_sesudah:
                aset.status = "Rusak"

            db.session.commit()
            return jsonify({"success": True, "data": mutasi.to_dict(), "aset": aset.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/aset/<int:id_aset>/lampu", methods=["GET"])
    @jwt_required
    def list_lampu_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        return jsonify({"success": True, "data": [l.to_dict() for l in aset.lampu.all()]})

    @app.route("/api/aset/suggest-kode", methods=["GET"])
    @jwt_required
    def suggest_kode_aset():
        kode_kategori = request.args.get("kategori", "").strip().upper()
        kode_wilayah = request.args.get("wilayah", "").strip().upper()
        tahun = request.args.get("tahun", type=int)

        if not kode_kategori or not kode_wilayah or not tahun:
            return jsonify({"success": False, "error": "Parameter wajib: kategori, wilayah, tahun"}), 400

        kat = KategoriPJU.query.filter_by(kode=kode_kategori, aktif=True).first()
        if not kat:
            return jsonify({"success": False, "error": f"Kategori '{kode_kategori}' tidak ditemukan atau tidak aktif"}), 404

        wil = Wilayah.query.filter_by(kode_wilayah=kode_wilayah).first()
        if not wil:
            return jsonify({"success": False, "error": f"Wilayah '{kode_wilayah}' tidak ditemukan"}), 404

        suggest, existing_count = AsetPJU.generate_suggest_kode(kode_kategori, kode_wilayah, tahun)
        return jsonify({
            "success": True,
            "suggest": suggest,
            "existing_count": existing_count,
            "kategori": kat.to_dict(),
            "wilayah": wil.to_dict(),
        })

    @app.route("/api/aset/cek-kode", methods=["GET"])
    @jwt_required
    def cek_kode_aset():
        kode = request.args.get("kode", "").strip().upper()
        if not kode:
            return jsonify({"success": False, "error": "Parameter 'kode' wajib"}), 400
        if not REGEX_KODE_ASET.match(kode):
            return jsonify({
                "success": True,
                "tersedia": False,
                "alasan": "format_invalid",
                "pesan": "Format tidak valid. Gunakan: PJUP-UH2-26-001",
            })
        existing = AsetPJU.query.filter_by(kode_aset=kode).first()
        if existing:
            return jsonify({
                "success": True,
                "tersedia": False,
                "alasan": "sudah_dipakai",
                "dipakai_oleh": existing.alamat,
                "id_aset": existing.id_aset,
            })
        return jsonify({"success": True, "tersedia": True})

    @app.route("/api/kategori-pju", methods=["GET"])
    def list_kategori_pju():
        semua = request.args.get("semua", "false").lower() == "true"
        q = KategoriPJU.query
        if not semua:
            q = q.filter_by(aktif=True)
        data = [k.to_dict() for k in q.order_by(KategoriPJU.urutan, KategoriPJU.kode).all()]
        return jsonify({"success": True, "total": len(data), "data": data})

    @app.route("/api/kategori-pju", methods=["POST"])
    @role_required("admin")
    def create_kategori_pju():
        body = request.get_json(force=True)
        kode = body.get("kode", "").strip().upper()
        nama = body.get("nama", "").strip()
        if not kode or not nama:
            return jsonify({"success": False, "error": "kode dan nama wajib diisi"}), 400
        if KategoriPJU.query.filter_by(kode=kode).first():
            return jsonify({"success": False, "error": f"Kode '{kode}' sudah digunakan"}), 409
        try:
            kat = KategoriPJU(
                kode=kode, nama=nama,
                deskripsi=body.get("deskripsi"),
                aktif=body.get("aktif", True),
                urutan=body.get("urutan", 0),
            )
            db.session.add(kat)
            db.session.commit()
            return jsonify({"success": True, "data": kat.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/kategori-pju/<int:id_kat>", methods=["PUT"])
    @role_required("admin")
    def update_kategori_pju(id_kat):
        kat = KategoriPJU.query.get(id_kat)
        if not kat:
            return jsonify({"success": False, "error": "Kategori tidak ditemukan"}), 404
        body = request.get_json(force=True)
        try:
            if "nama" in body:
                kat.nama = body["nama"].strip()
            if "deskripsi" in body:
                kat.deskripsi = body["deskripsi"]
            if "aktif" in body:
                kat.aktif = bool(body["aktif"])
            if "urutan" in body:
                kat.urutan = int(body["urutan"])
            db.session.commit()
            return jsonify({"success": True, "data": kat.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/kategori-pju/<int:id_kat>", methods=["DELETE"])
    @role_required("admin")
    def delete_kategori_pju(id_kat):
        kat = KategoriPJU.query.get(id_kat)
        if not kat:
            return jsonify({"success": False, "error": "Kategori tidak ditemukan"}), 404
        if kat.aset.count() > 0:
            kat.aktif = False
            db.session.commit()
            return jsonify({"success": True, "pesan": f"Kategori dinonaktifkan (ada {kat.aset.count()} aset terkait)"})
        try:
            db.session.delete(kat)
            db.session.commit()
            return jsonify({"success": True, "pesan": "Kategori dihapus"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/laporan", methods=["GET"])
    @jwt_required
    def list_laporan():
        q = LaporanKerja.query
        status_filter = request.args.get("status")
        if status_filter:
            q = q.filter(LaporanKerja.status == status_filter)
        data = [l.to_dict(Config.BOBOT_KATEGORI_JALAN) for l in q.all()]
        data.sort(key=lambda x: (-x["skor_prioritas"], x["tanggal_lapor"]))
        return jsonify({"success": True, "data": data})

    @app.route("/api/laporan", methods=["POST"])
    @jwt_required
    def create_laporan():
        body = request.get_json(force=True)
        aset = AsetPJU.query.get(body.get("id_aset"))
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        try:
            laporan = LaporanKerja(
                id_aset=aset.id_aset,
                kategori_jalan_snap=aset.kategori_jalan,
                sub_kategori_lainnya_snap=aset.sub_kategori_lainnya,
                status="Baru", catatan=body.get("catatan"),
            )
            aset.status = "Rusak"
            db.session.add(laporan)
            db.session.commit()
            return jsonify({"success": True, "data": laporan.to_dict(Config.BOBOT_KATEGORI_JALAN)}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/laporan/<int:id_laporan>/status", methods=["PATCH"])
    @role_required("koordinator", "admin")
    def update_status_laporan(id_laporan):
        laporan = LaporanKerja.query.get(id_laporan)
        if not laporan:
            return jsonify({"success": False, "error": "Laporan tidak ditemukan"}), 404
        status_baru = request.form.get("status")
        tindakan = request.form.get("tindakan_perbaikan")
        id_komponen = request.form.get("id_komponen_pins", type=int)
        qty_komponen = request.form.get("qty_komponen", default=1, type=int)
        id_teknisi = request.form.get("id_teknisi", type=int)
        foto = request.files.get("foto_bukti")
        try:
            if foto and allowed_file(foto.filename):
                laporan.foto_bukti = save_upload(foto, app.config["UPLOAD_FOLDER"])
            laporan.tindakan_perbaikan = tindakan
            laporan.id_teknisi = id_teknisi
            laporan.status = status_baru or laporan.status
            warna_status = {"Dalam Pengerjaan": "Dalam Pengerjaan", "Selesai": "Menyala"}
            if laporan.status in warna_status:
                laporan.aset.status = warna_status[laporan.status]
            if status_baru == "Selesai" and id_komponen:
                komponen = StokPins.query.with_for_update().get(id_komponen)
                if not komponen:
                    raise ValueError("Komponen PINS tidak ditemukan")
                if komponen.stok_qty < qty_komponen:
                    raise ValueError(f"Stok tidak cukup (sisa {komponen.stok_qty})")
                komponen.stok_qty -= qty_komponen
                laporan.id_komponen_pins = id_komponen
                laporan.qty_komponen = qty_komponen
            if laporan.status == "Selesai":
                laporan.tanggal_selesai = datetime.utcnow()
            db.session.commit()
            return jsonify({"success": True, "data": laporan.to_dict(Config.BOBOT_KATEGORI_JALAN)})
        except ValueError as ve:
            db.session.rollback()
            return jsonify({"success": False, "error": str(ve)}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/pins", methods=["GET"])
    @jwt_required
    def list_pins():
        return jsonify({"success": True, "data": [p.to_dict() for p in StokPins.query.all()]})

    @app.route("/api/pins/<int:id_pins>", methods=["GET"])
    @jwt_required
    def get_pins(id_pins):
        komponen = StokPins.query.get(id_pins)
        if not komponen:
            return jsonify({"success": False, "error": "Komponen tidak ditemukan"}), 404
        return jsonify({"success": True, "data": komponen.to_dict()})

    @app.route("/api/pins", methods=["POST"])
    @role_required("koordinator", "admin")
    def create_pins():
        body = request.get_json(force=True)
        nama = body.get("nama_komponen", "").strip()
        if not nama:
            return jsonify({"success": False, "error": "nama_komponen wajib diisi"}), 400
        try:
            komponen = StokPins(
                nama_komponen=nama,
                satuan=body.get("satuan", "pcs"),
                stok_qty=body.get("stok_qty", 0),
                stok_minimum=body.get("stok_minimum", 0),
                keterangan=body.get("keterangan"),
            )
            db.session.add(komponen)
            db.session.commit()
            return jsonify({"success": True, "data": komponen.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/pins/<int:id_pins>", methods=["PATCH"])
    @role_required("koordinator", "admin")
    def update_pins(id_pins):
        komponen = StokPins.query.get(id_pins)
        if not komponen:
            return jsonify({"success": False, "error": "Komponen tidak ditemukan"}), 404
        body = request.get_json(force=True)
        try:
            for field in ["nama_komponen", "satuan", "stok_qty", "stok_minimum", "keterangan"]:
                if field in body:
                    setattr(komponen, field, body[field])
            db.session.commit()
            return jsonify({"success": True, "data": komponen.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/wilayah", methods=["GET"])
    def list_wilayah():
        q = Wilayah.query
        kemantren_filter = request.args.get("kemantren")
        if kemantren_filter:
            q = q.filter(Wilayah.nama_kemantren.ilike(f"%{kemantren_filter}%"))
        data = [w.to_dict() for w in q.order_by(Wilayah.kode_wilayah).all()]
        return jsonify({"success": True, "total": len(data), "data": data})

    @app.route("/api/wilayah/<string:kode>", methods=["GET"])
    def get_wilayah(kode):
        wilayah = Wilayah.query.filter_by(kode_wilayah=kode.upper()).first()
        if not wilayah:
            return jsonify({"success": False, "error": f"Wilayah '{kode}' tidak ditemukan"}), 404
        result = wilayah.to_dict()
        result["jumlah_aset"] = wilayah.aset.count()
        result["jumlah_panel"] = wilayah.panel.count()
        return jsonify({"success": True, "data": result})

    @app.route("/api/regu", methods=["GET"])
    @jwt_required
    def list_regu():
        return jsonify({"success": True, "data": [r.to_dict() for r in Regu.query.filter_by(status_aktif=True).all()]})

    @app.route("/api/regu/<int:id_regu>", methods=["GET"])
    @jwt_required
    def get_regu(id_regu):
        regu = Regu.query.get(id_regu)
        if not regu:
            return jsonify({"success": False, "error": "Regu tidak ditemukan"}), 404
        return jsonify({"success": True, "data": regu.to_dict()})

    @app.route("/api/regu/<int:id_regu>/anggota", methods=["GET"])
    @jwt_required
    def list_anggota_regu(id_regu):
        regu = Regu.query.get(id_regu)
        if not regu:
            return jsonify({"success": False, "error": "Regu tidak ditemukan"}), 404
        return jsonify({"success": True, "regu": regu.nama_regu, "data": [p.to_dict() for p in regu.anggota.filter_by(status_aktif=True).all()]})

    @app.route("/api/laporan-kerusakan", methods=["GET"])
    @jwt_required
    def list_laporan_kerusakan():
        q = LaporanKerusakan.query
        if request.args.get("status"):
            q = q.filter(LaporanKerusakan.status_laporan == request.args.get("status"))
        if request.args.get("sumber"):
            q = q.filter(LaporanKerusakan.sumber_laporan == request.args.get("sumber"))
        if request.args.get("id_aset", type=int):
            q = q.filter(LaporanKerusakan.id_aset == request.args.get("id_aset", type=int))
        q = q.order_by(LaporanKerusakan.tanggal_lapor.desc())
        items, meta = _paginate(q)
        return jsonify({"success": True, "meta": meta, "data": [l.to_dict() for l in items]})

    @app.route("/api/laporan-kerusakan/<int:id_laporan>", methods=["GET"])
    @jwt_required
    def get_laporan_kerusakan(id_laporan):
        laporan = LaporanKerusakan.query.get(id_laporan)
        if not laporan:
            return jsonify({"success": False, "error": "Laporan tidak ditemukan"}), 404
        return jsonify({"success": True, "data": laporan.to_dict()})

    @app.route("/api/laporan-kerusakan", methods=["POST"])
    @jwt_required
    def create_laporan_kerusakan():
        id_aset = request.form.get("id_aset", type=int)
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        foto = request.files.get("foto")
        foto_url = save_upload(foto, app.config["UPLOAD_FOLDER"]) if foto and allowed_file(foto.filename) else None
        try:
            laporan = LaporanKerusakan(
                id_aset=id_aset,
                id_user=request.form.get("id_user", type=int),
                deskripsi_kerusakan=request.form.get("deskripsi_kerusakan", ""),
                foto_url=foto_url,
                sumber_laporan=request.form.get("sumber_laporan", "Lapangan"),
                status_laporan="Baru",
            )
            aset.status = "Rusak"
            db.session.add(laporan)
            db.session.commit()
            return jsonify({"success": True, "data": laporan.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/laporan-kerusakan/<int:id_laporan>/status", methods=["PATCH"])
    @role_required("koordinator", "admin")
    def update_status_laporan_kerusakan(id_laporan):
        laporan = LaporanKerusakan.query.get(id_laporan)
        if not laporan:
            return jsonify({"success": False, "error": "Laporan tidak ditemukan"}), 404
        body = request.get_json(force=True)
        try:
            laporan.status_laporan = body.get("status_laporan", laporan.status_laporan)
            db.session.commit()
            return jsonify({"success": True, "data": laporan.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/pemeliharaan", methods=["GET"])
    @jwt_required
    def list_pemeliharaan():
        q = RiwayatPemeliharaan.query
        if request.args.get("id_aset", type=int):
            q = q.filter(RiwayatPemeliharaan.id_aset == request.args.get("id_aset", type=int))
        if request.args.get("id_regu", type=int):
            q = q.filter(RiwayatPemeliharaan.id_regu == request.args.get("id_regu", type=int))
        if request.args.get("status"):
            q = q.filter(RiwayatPemeliharaan.status_pekerjaan == request.args.get("status"))
        q = q.order_by(RiwayatPemeliharaan.tanggal_pengerjaan.desc())
        items, meta = _paginate(q)
        return jsonify({"success": True, "meta": meta, "data": [p.to_dict() for p in items]})

    @app.route("/api/pemeliharaan/<int:id_pemeliharaan>", methods=["GET"])
    @jwt_required
    def get_pemeliharaan(id_pemeliharaan):
        p = RiwayatPemeliharaan.query.get(id_pemeliharaan)
        if not p:
            return jsonify({"success": False, "error": "Data tidak ditemukan"}), 404
        return jsonify({"success": True, "data": p.to_dict()})

    @app.route("/api/pemeliharaan", methods=["POST"])
    @role_required("regu", "koordinator", "admin")
    def create_pemeliharaan():
        id_aset = request.form.get("id_aset", type=int)
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        foto_sebelum = request.files.get("foto_sebelum")
        foto_sesudah = request.files.get("foto_sesudah")
        foto_sebelum_url = save_upload(foto_sebelum, app.config["UPLOAD_FOLDER"]) if foto_sebelum and allowed_file(foto_sebelum.filename) else None
        foto_sesudah_url = save_upload(foto_sesudah, app.config["UPLOAD_FOLDER"]) if foto_sesudah and allowed_file(foto_sesudah.filename) else None
        try:
            pemeliharaan = RiwayatPemeliharaan(
                id_aset=id_aset,
                id_regu=request.form.get("id_regu", type=int),
                id_user=request.form.get("id_user", type=int),
                id_laporan=request.form.get("id_laporan", type=int),
                jenis_pekerjaan=request.form.get("jenis_pekerjaan", ""),
                deskripsi_pekerjaan=request.form.get("deskripsi_pekerjaan"),
                foto_sebelum=foto_sebelum_url,
                foto_sesudah=foto_sesudah_url,
                status_pekerjaan=request.form.get("status_pekerjaan", "Dalam Pengerjaan"),
            )
            id_laporan_int = request.form.get("id_laporan", type=int)
            if id_laporan_int:
                lap = LaporanKerusakan.query.get(id_laporan_int)
                if lap:
                    lap.status_laporan = "Diproses"
            if pemeliharaan.status_pekerjaan == "Selesai":
                aset.status = "Menyala"
                if id_laporan_int:
                    lap = LaporanKerusakan.query.get(id_laporan_int)
                    if lap:
                        lap.status_laporan = "Selesai"
            db.session.add(pemeliharaan)
            db.session.commit()
            return jsonify({"success": True, "data": pemeliharaan.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/pemeliharaan/<int:id_pemeliharaan>/status", methods=["PATCH"])
    @role_required("regu", "koordinator", "admin")
    def update_status_pemeliharaan(id_pemeliharaan):
        p = RiwayatPemeliharaan.query.get(id_pemeliharaan)
        if not p:
            return jsonify({"success": False, "error": "Data tidak ditemukan"}), 404
        status_baru = request.form.get("status_pekerjaan")
        foto_sesudah = request.files.get("foto_sesudah")
        try:
            if foto_sesudah and allowed_file(foto_sesudah.filename):
                p.foto_sesudah = save_upload(foto_sesudah, app.config["UPLOAD_FOLDER"])
            if status_baru:
                p.status_pekerjaan = status_baru
            if status_baru == "Selesai":
                aset = AsetPJU.query.get(p.id_aset)
                if aset:
                    aset.status = "Menyala"
                if p.id_laporan:
                    lap = LaporanKerusakan.query.get(p.id_laporan)
                    if lap:
                        lap.status_laporan = "Selesai"
            db.session.commit()
            return jsonify({"success": True, "data": p.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/dashboard/summary", methods=["GET"])
    @jwt_required
    def dashboard_summary():
        total_aset = AsetPJU.query.count()
        total_rusak = AsetPJU.query.filter_by(status="Rusak").count()
        total_pengerjaan = AsetPJU.query.filter_by(status="Dalam Pengerjaan").count()
        tiket_baru = LaporanKerusakan.query.filter_by(status_laporan="Baru").count()
        tiket_diproses = LaporanKerusakan.query.filter_by(status_laporan="Diproses").count()
        stok_kritis = StokPins.query.filter(StokPins.stok_qty <= StokPins.stok_minimum).count()
        return jsonify({
            "success": True,
            "data": {
                "total_aset": total_aset,
                "total_rusak": total_rusak,
                "total_pengerjaan": total_pengerjaan,
                "tiket_baru": tiket_baru,
                "tiket_diproses": tiket_diproses,
                "stok_kritis": stok_kritis,
            }
        })

    @app.route("/uploads/<filename>")
    def serve_upload(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"success": True, "status": "ok", "time": datetime.utcnow().isoformat()})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
