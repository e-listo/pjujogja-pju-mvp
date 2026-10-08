"""
Tes jwt_required: akun diperiksa ulang ke database pada setiap permintaan.
Nama berkas mengikuti pola test_aset_bulk*.py agar ikut dijalankan CI.
Memakai aplikasi Flask mini + SQLite in-memory (hanya tabel pengguna).
"""
import unittest
from datetime import datetime, timedelta, timezone

import jwt
from flask import Flask, g, jsonify
from werkzeug.security import generate_password_hash

from auth_routes import _buat_token, auth_bp, jwt_required, role_required
from models import Pengguna, db

SECRET = "rahasia-uji"


class AuthStatusAktifTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET=SECRET,
            JWT_EXP_HOURS=1,
        )
        db.init_app(app)
        app.register_blueprint(auth_bp)

        @app.route("/uji/terlindungi")
        @jwt_required
        def terlindungi():
            return jsonify(peran=g.user_payload["peran"])

        @app.route("/uji/khusus-admin")
        @role_required("admin")
        def khusus_admin():
            return jsonify(ok=True)

        self.app = app
        self.ctx = app.app_context()
        self.ctx.push()
        Pengguna.__table__.create(bind=db.engine)
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        Pengguna.__table__.drop(bind=db.engine)
        self.ctx.pop()

    def _akun(self, username, peran="teknisi", aktif=True):
        akun = Pengguna(
            nama_lengkap=username.title(),
            username=username,
            password_hash=generate_password_hash("rahasia123"),
            peran=peran,
            status_aktif=aktif,
        )
        db.session.add(akun)
        db.session.commit()
        return akun

    def _header(self, akun):
        token, _ = _buat_token(akun)
        return {"Authorization": f"Bearer {token}"}

    def _token_manual(self, klaim):
        klaim = dict(klaim)
        klaim["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode(klaim, SECRET, algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    def test_akun_aktif_diterima(self):
        akun = self._akun("budi")
        resp = self.client.get("/uji/terlindungi", headers=self._header(akun))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["peran"], "teknisi")

    def test_akun_dinonaktifkan_langsung_ditolak(self):
        akun = self._akun("sari")
        header = self._header(akun)
        self.assertEqual(self.client.get("/uji/terlindungi", headers=header).status_code, 200)

        akun.status_aktif = False
        db.session.commit()

        resp = self.client.get("/uji/terlindungi", headers=header)
        self.assertEqual(resp.status_code, 401)
        self.assertIn("tidak aktif", resp.get_json()["error"])

    def test_akun_dihapus_ditolak(self):
        akun = self._akun("hapus")
        header = self._header(akun)
        db.session.delete(akun)
        db.session.commit()
        self.assertEqual(self.client.get("/uji/terlindungi", headers=header).status_code, 401)

    def test_perubahan_peran_langsung_berlaku(self):
        akun = self._akun("naik", peran="teknisi")
        header = self._header(akun)
        self.assertEqual(self.client.get("/uji/khusus-admin", headers=header).status_code, 403)

        akun.peran = "admin"
        db.session.commit()
        self.assertEqual(self.client.get("/uji/khusus-admin", headers=header).status_code, 200)

        akun.peran = "teknisi"
        db.session.commit()
        self.assertEqual(self.client.get("/uji/khusus-admin", headers=header).status_code, 403)

    def test_token_lama_tanpa_sub_dicari_lewat_username(self):
        akun = self._akun("lama")
        header = self._token_manual({"username": akun.username, "peran": "admin"})
        resp = self.client.get("/uji/terlindungi", headers=header)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["peran"], "teknisi")

    def test_klaim_peran_di_token_tidak_dipercaya(self):
        akun = self._akun("palsu", peran="teknisi")
        header = self._token_manual(
            {"sub": str(akun.id_pengguna), "username": akun.username, "peran": "admin"}
        )
        resp = self.client.get("/uji/khusus-admin", headers=header)
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
