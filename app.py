"""
app.py — Entry point Flask untuk pjujogja.id
Kategori jalan mengikuti Perwal Kota Yogyakarta No. 50/2022 (Jalan Kota,
Jalan Lingkungan, Jalan Lingkungan Kampung, Lainnya).
"""
import os
import uuid
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from models import db, AsetPJU, LaporanKerja, StokPins, Pengguna, SUB_KATEGORI_LAINNYA


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    # -------------------------------------------------------------
    # 1) ASET PJU
    # -------------------------------------------------------------
    @app.route("/api/aset", methods=["GET"])
    def list_aset():
        q = AsetPJU.query
        status_filter = request.args.get("status")
        kategori_filter = request.args.get("kategori_jalan")
        if status_filter:
            q = q.filter(AsetPJU.status == status_filter)
        else:
            q = q.filter(AsetPJU.status.in_(["Rusak", "Dalam Pengerjaan", "Menyala"]))
        if kategori_filter:
            q = q.filter(AsetPJU.kategori_jalan == kategori_filter)
        data = [a.to_dict() for a in q.all()]
        return jsonify({"success": True, "data": data})

    @app.route("/api/aset", methods=["POST"])
    def create_aset():
        body = request.get_json(force=True)
        kategori_jalan = body.get("kategori_jalan", "Jalan Lingkungan")
        sub_kategori = body.get("sub_kategori_lainnya")

        if kategori_jalan == "Lainnya" and sub_kategori not in SUB_KATEGORI_LAINNYA:
            return jsonify({
                "success": False,
                "error": f"Kategori 'Lainnya' wajib memilih sub_kategori_lainnya: {SUB_KATEGORI_LAINNYA}"
            }), 400
        if kategori_jalan != "Lainnya":
            sub_kategori = None

        try:
            aset = AsetPJU(
                kode_aset=body["kode_aset"],
                alamat=body["alamat"],
                lokasi_lat=body["lat"],
                lokasi_lng=body["lng"],
                kategori_jalan=kategori_jalan,
                sub_kategori_lainnya=sub_kategori,
                jenis_lampu=body.get("jenis_lampu"),
                watt=body.get("watt"),
                status=body.get("status", "Menyala"),
            )
            db.session.add(aset)
            db.session.commit()
            return jsonify({"success": True, "data": aset.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    # -------------------------------------------------------------
    # 2) LAPORAN KERJA — Ticketing & Prioritas Linier
    # -------------------------------------------------------------
    @app.route("/api/laporan", methods=["GET"])
    def list_laporan():
        q = LaporanKerja.query
        status_filter = request.args.get("status")
        if status_filter:
            q = q.filter(LaporanKerja.status == status_filter)
        laporan_list = q.all()
        data = [l.to_dict(Config.BOBOT_KATEGORI_JALAN) for l in laporan_list]
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
                status="Baru",
                catatan=body.get("catatan"),
            )
            aset.status = "Rusak"
            db.session.add(laporan)
            db.session.commit()
            return jsonify({"success": True, "data": laporan.to_dict(Config.BOBOT_KATEGORI_JALAN)}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    # -------------------------------------------------------------
    # 3) UPDATE STATUS OLEH REGU LAPANGAN + TRIGGER POTONG STOK PINS
    # -------------------------------------------------------------
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
                ext = foto.filename.rsplit(".", 1)[1].lower()
                nama_file = f"{uuid.uuid4().hex}.{ext}"
                foto.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(nama_file)))
                laporan.foto_bukti = nama_file

            laporan.tindakan_perbaikan = tindakan
            laporan.id_teknisi = id_teknisi
            laporan.status = status_baru or laporan.status

            warna_status = {
                "Dalam Pengerjaan": "Dalam Pengerjaan",
                "Selesai": "Menyala",
            }
            if laporan.status in warna_status:
                laporan.aset.status = warna_status[laporan.status]

            if status_baru == "Selesai" and id_komponen:
                komponen = StokPins.query.get(id_komponen)
                if not komponen:
                    raise ValueError("Komponen PINS tidak ditemukan")
                if komponen.stok_qty < qty_komponen:
                    raise ValueError(
                        f"Stok {komponen.nama_komponen} tidak cukup (sisa {komponen.stok_qty})"
                    )
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

    # -------------------------------------------------------------
    # 4) STOK PINS
    # -------------------------------------------------------------
    @app.route("/api/pins", methods=["GET"])
    def list_pins():
        data = [p.to_dict() for p in StokPins.query.all()]
        return jsonify({"success": True, "data": data})

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
