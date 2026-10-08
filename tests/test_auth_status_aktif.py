"""
Tes jwt_required: akun diperiksa ulang ke database pada setiap permintaan.
Memakai aplikasi Flask mini + SQLite in-memory (hanya tabel pengguna).
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from flask import Flask, g, jsonify
from werkzeug.security import generate_password_hash

from auth_routes import _buat_token, auth_bp, jwt_required, role_required
from models import Pengguna, db

SECRET = "rahasia-uji"


@pytest.fixture()
def app():
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

    with app.app_context():
        Pengguna.__table__.create(bind=db.engine)
        yield app
        db.session.remove()
        Pengguna.__table__.drop(bind=db.engine)


def _akun(username, peran="teknisi", aktif=True):
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


def _header(akun):
    token, _ = _buat_token(akun)
    return {"Authorization": f"Bearer {token}"}


def test_akun_aktif_diterima(app):
    akun = _akun("budi")
    resp = app.test_client().get("/uji/terlindungi", headers=_header(akun))
    assert resp.status_code == 200
    assert resp.get_json()["peran"] == "teknisi"


def test_akun_dinonaktifkan_langsung_ditolak(app):
    akun = _akun("sari")
    header = _header(akun)
    client = app.test_client()
    assert client.get("/uji/terlindungi", headers=header).status_code == 200

    akun.status_aktif = False
    db.session.commit()

    resp = client.get("/uji/terlindungi", headers=header)
    assert resp.status_code == 401
    assert "tidak aktif" in resp.get_json()["error"]


def test_akun_dihapus_ditolak(app):
    akun = _akun("hapus")
    header = _header(akun)
    db.session.delete(akun)
    db.session.commit()
    assert app.test_client().get("/uji/terlindungi", headers=header).status_code == 401


def test_perubahan_peran_langsung_berlaku(app):
    akun = _akun("naik", peran="teknisi")
    header = _header(akun)
    client = app.test_client()
    assert client.get("/uji/khusus-admin", headers=header).status_code == 403

    akun.peran = "admin"
    db.session.commit()
    assert client.get("/uji/khusus-admin", headers=header).status_code == 200

    akun.peran = "teknisi"
    db.session.commit()
    assert client.get("/uji/khusus-admin", headers=header).status_code == 403


def test_token_lama_tanpa_sub_dicari_lewat_username(app):
    akun = _akun("lama")
    token = jwt.encode(
        {
            "username": akun.username,
            "peran": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        SECRET,
        algorithm="HS256",
    )
    resp = app.test_client().get(
        "/uji/terlindungi", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["peran"] == "teknisi"


def test_klaim_peran_di_token_tidak_dipercaya(app):
    akun = _akun("palsu", peran="teknisi")
    token = jwt.encode(
        {
            "sub": str(akun.id_pengguna),
            "username": akun.username,
            "peran": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        SECRET,
        algorithm="HS256",
    )
    resp = app.test_client().get(
        "/uji/khusus-admin", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
