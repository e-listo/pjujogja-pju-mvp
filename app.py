"""
app.py — Entry point Flask untuk api.pjujogja.id
Kategori jalan mengikuti Perwal Kota Yogyakarta No. 50/2022 (Jalan Kota,
Jalan Lingkungan, Jalan Lingkungan Kampung, Lainnya).

Fase 2: Tambah endpoint Wilayah, Regu, LaporanKerusakan, RiwayatPemeliharaan.
Fase 4: Autentikasi JWT.
"""
import os
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
)
from auth_routes import auth_bp


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_upload(file_obj, upload_folder):
    ext = file_obj.filename.rsplit(".", 1)[1].lower()
    nama_file = f"{uuid.uuid4().hex}.{ext}"
    file_obj.save(os.path.join(upload_folder, secure_filename(nama_file)))
    return nama_file


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    # Daftarkan blueprint autentikasi
    app.register_blueprint(auth_bp)

    # =================================================================
    # FASE 1 — Endpoint yang sudah ada (tidak diubah)
    # =================================================================

    @app.route("/api/aset", methods=["GET"])
    def list_aset():
        q = AsetPJU.query
        status_filter = request.args.get("status")
        kategori_filter = request.args.get("kategori_jalan")
        id_wilayah_filter = request.args.get("id_wilayah", type=int)
        if status_filter:
            q = q.filter(AsetPJU.status == status_filter)
        else:
            q = q.filter(AsetPJU.status.in_(["Rusak", "Dalam Pengerjaan", "Menyala"]))
        if kategori_filter:
            q = q.filter(AsetPJU.kategori_jalan == kategori_filter)
        if id_wilayah_filter:
            q = q.filter(AsetPJU.id_wilayah == id_wilayah_filter)
        data = [a.to_dict() for a in q.all()]
        return jsonify({"success": True, "data": data})

    @app.route("/api/aset", methods=["POST"])
    def create_aset():
        body = request.get_json(force=True)
        kategori_jalan = body.get("kategori_jalan", "Jalan Lingkungan")
        sub_kategori = body.get("sub_kategori_lainnya")
        if kategori_jalan == "Lainnya" and sub_kategori not in SUB_KATEGORI_LAINNYA:
            return jsonify({"success": False, "error": f"sub_kategori_lainnya wajib: {SUB_KATEGORI_LAINNYA}"}), 400
        if kategori_jalan != "Lainnya":
            sub_kategori = None
        try:
            aset = AsetPJU(
                kode_aset=body["kode_aset"], alamat=body["alamat"],
                lokasi_lat=body["lat"], lokasi_lng=body["lng"],
                kategori_jalan=kategori_jalan, sub_kategori_lainnya=sub_kategori,
                id_wilayah=body.get("id_wilayah"), id_panel=body.get("id_panel"),
                jenis_tiang=body.get("jenis_tiang"), tinggi_meter=body.get("tinggi_meter"),
                jenis_lampu=body.get("jenis_lampu"), watt=body.get("watt"),
                status=body.get("status", "Menyala"),
            )
            db.session.add(aset)
            db.session.commit()
            return jsonify({"success": True, "data": aset.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/aset/<int:id_aset>/lampu", methods=["GET"])
    def list_lampu_aset(id_aset):
        aset = AsetPJU.query.get(id_aset)
        if not aset:
            return jsonify({"success": False, "error": "Aset tidak ditemukan"}), 404
        return jsonify({"success": True, "data": [l.to_dict() for l in aset.lampu.all()]})

    @app.route("/api/laporan", methods=["GET"])
    def list_laporan():
        q = LaporanKerja.query
        status_filter = request.args.get("status")
        if status_filter:
            q = q.filter(LaporanKerja.status == status_filter)
        data = [l.to_dict(Config.BOBOT_KATEGORI_JALAN) for l in q.all()]
        data.sort(key=lambda x: (-x["skor_prioritas"], x["tanggal_lapor"]))
        return jsonify({"success": True, "data": data})

    @app.route("/api/laporan", methods=["POST"])
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
                komponen = StokPins.query.get(id_komponen)
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
    def list_pins():
        return jsonify({"success": True, "data": [p.to_dict() for p in StokPins.query.all()]})

    # =================================================================
    # FASE 2
    # =================================================================
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
    def list_regu():
        return jsonify({"success": True, "data": [r.to_dict() for r in Regu.query.filter_by(status_aktif=True).all()]})

    @app.route("/api/regu/<int:id_regu>/anggota", methods=["GET"])
    def list_anggota_regu(id_regu):
        regu = Regu.query.get(id_regu)
        if not regu:
            return jsonify({"success": False, "error": "Regu tidak ditemukan"}), 404
        return jsonify({"success": True, "regu": regu.nama_regu, "data": [p.to_dict() for p in regu.anggota.filter_by(status_aktif=True).all()]})

    @app.route("/api/laporan-kerusakan", methods=["GET"])
    def list_laporan_kerusakan():
        q = LaporanKerusakan.query
        if request.args.get("status"):
            q = q.filter(LaporanKerusakan.status_laporan == request.args.get("status"))
        if request.args.get("sumber"):
            q = q.filter(LaporanKerusakan.sumber_laporan == request.args.get("sumber"))
        if request.args.get("id_aset", type=int):
            q = q.filter(LaporanKerusakan.id_aset == request.args.get("id_aset", type=int))
        data = [l.to_dict() for l in q.order_by(LaporanKerusakan.tanggal_lapor.desc()).all()]
        return jsonify({"success": True, "total": len(data), "data": data})

    @app.route("/api/laporan-kerusakan", methods=["POST"])
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
    def list_pemeliharaan():
        q = RiwayatPemeliharaan.query
        if request.args.get("id_aset", type=int):
            q = q.filter(RiwayatPemeliharaan.id_aset == request.args.get("id_aset", type=int))
        if request.args.get("id_regu", type=int):
            q = q.filter(RiwayatPemeliharaan.id_regu == request.args.get("id_regu", type=int))
        if request.args.get("status"):
            q = q.filter(RiwayatPemeliharaan.status_pekerjaan == request.args.get("status"))
        data = [p.to_dict() for p in q.order_by(RiwayatPemeliharaan.tanggal_pengerjaan.desc()).all()]
        return jsonify({"success": True, "total": len(data), "data": data})

    @app.route("/api/pemeliharaan", methods=["POST"])
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
