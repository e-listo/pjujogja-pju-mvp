"""
auth_routes.py — Blueprint autentikasi JWT dan manajemen pengguna untuk PIJAR
Endpoint autentikasi:
  POST /api/auth/login          — return access token
  POST /api/auth/logout         — blacklist token aktif (logout)
  GET  /api/auth/me             — info pengguna dari token
  POST /api/auth/ubah-password  — pengguna mengganti password sendiri
  POST /api/auth/seed           — buat akun admin pertama (sekali pakai, disabled di production)
Endpoint manajemen pengguna (khusus admin):
  GET        /api/pengguna                      — daftar, cari, saring, paginasi
  POST       /api/pengguna                      — buat akun (password diketik admin)
  GET        /api/pengguna/<id>                 — detail
  PUT/PATCH  /api/pengguna/<id>                 — ubah nama, username, peran, regu, no_hp, status_aktif
  POST       /api/pengguna/<id>/reset-password  — admin mengganti password akun
Aturan: tidak ada hapus (nonaktifkan saja); admin tidak boleh menonaktifkan atau
mengubah peran akunnya sendiri; regu boleh kosong dan bisa diganti kapan saja.
"""
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, request, jsonify, current_app, g
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Pengguna, Regu

auth_bp = Blueprint("auth", __name__)

# ------------------------------------------------------------------ #
# In-memory token blacklist dengan TTL cleanup
# Cocok untuk shared hosting single-process (Passenger WSGI).
# Fix #3: _cleanup_blacklist() dipanggil saat login untuk membuang
# JTI yang tokennya sudah expired agar set tidak tumbuh terus.
# ------------------------------------------------------------------ #
# Format: { jti: exp_timestamp }
_BLACKLIST: dict = {}


def _cleanup_blacklist():
    """Buang JTI yang sudah expired dari blacklist. Dipanggil saat login."""
    now = datetime.now(timezone.utc).timestamp()
    expired_keys = [jti for jti, exp in _BLACKLIST.items() if exp < now]
    for k in expired_keys:
        del _BLACKLIST[k]


# ------------------------------------------------------------------ #
# Helper: buat token
# ------------------------------------------------------------------ #
def _buat_token(pengguna):
    secret = current_app.config["JWT_SECRET"]
    exp    = datetime.now(timezone.utc) + timedelta(hours=current_app.config.get("JWT_EXP_HOURS", 12))
    payload = {
        "jti":      str(uuid.uuid4()),        # JWT ID unik — dipakai blacklist logout
        "sub":      str(pengguna.id_pengguna), # PyJWT >= 2.4.0 wajib string
        "username": pengguna.username,
        "peran":    pengguna.peran,
        "nama":     pengguna.nama_lengkap,
        "exp":      exp,
    }
    return jwt.encode(payload, secret, algorithm="HS256"), exp


# ------------------------------------------------------------------ #
# Helper: muat akun dari database berdasarkan isi token
# ------------------------------------------------------------------ #
def _muat_pengguna(payload):
    """
    Cari akun pemilik token. Utamakan klaim `sub` (id_pengguna).
    Token lama yang `sub`-nya bukan angka dicari lewat `username`.
    """
    sub = payload.get("sub")
    if sub is not None:
        try:
            return db.session.get(Pengguna, int(sub))
        except (TypeError, ValueError):
            pass
    username = payload.get("username")
    if username:
        return Pengguna.query.filter_by(username=username).first()
    return None


# ------------------------------------------------------------------ #
# Decorator: proteksi endpoint
# ------------------------------------------------------------------ #
def jwt_required(f):
    """
    Decorator — wajib login. Isi g.user_payload dan g.pengguna.

    Akun diperiksa ulang ke database pada setiap permintaan:
    - akun dihapus atau status_aktif = False  -> 401 (langsung, tanpa menunggu token habis)
    - peran, nama, dan username diambil dari database, sehingga perubahan
      peran oleh admin langsung berlaku tanpa login ulang.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Token tidak ditemukan"}), 401
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=["HS256"],
                options={"verify_sub": False},  # backward-compat token lama
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token kadaluarsa, silakan login ulang"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Token tidak valid"}), 401

        # Cek blacklist: token sudah di-logout?
        jti = payload.get("jti")
        if jti and jti in _BLACKLIST:
            return jsonify({"success": False, "error": "Token sudah tidak aktif, silakan login ulang"}), 401

        # Cek akun di database: masih ada dan aktif?
        pengguna = _muat_pengguna(payload)
        if pengguna is None or not pengguna.status_aktif:
            return jsonify({"success": False, "error": "Akun tidak aktif atau tidak ditemukan"}), 401

        payload = dict(payload)
        payload["peran"]    = pengguna.peran
        payload["nama"]     = pengguna.nama_lengkap
        payload["username"] = pengguna.username
        g.user_payload = payload
        g.pengguna     = pengguna
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """
    Decorator — batasi akses berdasarkan peran.

    Peran "regu" yang dipakai di app.py bukan nilai sah kolom Pengguna.peran
    (enum: admin, koordinator, teknisi). Regu pelaksana lapangan adalah akun
    "teknisi", jadi "regu" dipetakan ke "teknisi" di sini.
    """
    roles = tuple("teknisi" if r == "regu" else r for r in roles)

    def decorator(f):
        @wraps(f)
        @jwt_required
        def wrapper(*args, **kwargs):
            if g.user_payload.get("peran") not in roles:
                return jsonify({"success": False, "error": "Akses ditolak"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ------------------------------------------------------------------ #
# ROUTES
# ------------------------------------------------------------------ #

@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    body     = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    if not username or not password:
        return jsonify({"success": False, "error": "Username dan password wajib diisi"}), 400

    pengguna = Pengguna.query.filter_by(username=username, status_aktif=True).first()
    if not pengguna or not check_password_hash(pengguna.password_hash, password):
        return jsonify({"success": False, "error": "Username atau password salah"}), 401

    # Fix #3: cleanup blacklist dari JTI expired setiap kali login
    _cleanup_blacklist()

    token, exp = _buat_token(pengguna)
    return jsonify({
        "success": True,
        "token":   token,
        "pengguna": {
            "id":       pengguna.id_pengguna,
            "nama":     pengguna.nama_lengkap,
            "username": pengguna.username,
            "peran":    pengguna.peran,
        }
    })


@auth_bp.route("/api/auth/logout", methods=["POST"])
@jwt_required
def logout():
    """
    Blacklist token aktif sehingga tidak bisa dipakai lagi.
    Fix #3: simpan (jti, exp) — bukan hanya jti — agar cleanup TTL bisa bekerja.
    Frontend wajib hapus token dari localStorage/sessionStorage setelah ini.
    """
    jti = g.user_payload.get("jti")
    exp = g.user_payload.get("exp")  # Unix timestamp dari JWT
    if jti and exp:
        _BLACKLIST[jti] = exp
    return jsonify({
        "success": True,
        "pesan":   "Logout berhasil. Silakan hapus token di sisi klien."
    })


@auth_bp.route("/api/auth/me", methods=["GET"])
@jwt_required
def me():
    return jsonify({"success": True, "data": g.user_payload})


@auth_bp.route("/api/auth/seed", methods=["POST"])
def seed_admin():
    """
    Buat akun admin pertama.
    Dinonaktifkan otomatis jika env SEED_ENABLED != '1'.
    Set SEED_ENABLED=1 hanya saat setup awal, lalu hapus dari env.
    """
    if os.environ.get("SEED_ENABLED", "0") != "1":
        return jsonify({"success": False, "error": "Endpoint seed tidak aktif"}), 403

    secret_key = request.headers.get("X-Seed-Key", "")
    if secret_key != current_app.config.get("SEED_SECRET", "GANTI_INI"):
        return jsonify({"success": False, "error": "Seed key salah"}), 403

    if Pengguna.query.filter_by(peran="admin").first():
        return jsonify({"success": False, "error": "Akun admin sudah ada"}), 409

    body  = request.get_json(force=True)
    admin = Pengguna(
        nama_lengkap=body.get("nama_lengkap", "Administrator"),
        username=body.get("username", "admin"),
        password_hash=generate_password_hash(body.get("password", "pijar2026")),
        peran="admin",
        status_aktif=True,
    )
    db.session.add(admin)
    db.session.commit()
    return jsonify({"success": True, "message": f"Admin '{admin.username}' berhasil dibuat"}), 201


# ------------------------------------------------------------------ #
# MANAJEMEN PENGGUNA
# ------------------------------------------------------------------ #
PERAN_VALID  = ("admin", "koordinator", "teknisi")
PASSWORD_MIN = 8
PASSWORD_MAX = 128
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,50}$")
_NOHP_RE     = re.compile(r"^[0-9+()\s-]{5,20}$")


def _err(pesan, kode=400):
    return jsonify({"success": False, "error": pesan}), kode


def _body_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _audit(aksi, target):
    # Level WARNING agar pasti tercatat di stderr.log (INFO tidak diteruskan handler bawaan).
    pelaku = g.pengguna.username if getattr(g, "pengguna", None) else "?"
    current_app.logger.warning("AUDIT pengguna: %s | pelaku=%s | target=%s", aksi, pelaku, target)


def _peta_regu():
    return {r.id_regu: r.nama_regu for r in Regu.query.all()}


def _bentuk_pengguna(p, peta_regu):
    d = p.to_dict()
    d["nama_regu"]  = peta_regu.get(p.id_regu) if p.id_regu else None
    d["created_at"] = p.created_at.isoformat() if p.created_at else None
    return d


def _cek_password(pw):
    if not isinstance(pw, str) or len(pw) < PASSWORD_MIN:
        return f"Password minimal {PASSWORD_MIN} karakter"
    if len(pw) > PASSWORD_MAX:
        return f"Password maksimal {PASSWORD_MAX} karakter"
    return None


def _bersihkan_input(data, buat):
    """Validasi field profil. buat=True: nama_lengkap, username, peran wajib. Return (nilai, pesan_error)."""
    out = {}
    if buat or "nama_lengkap" in data:
        v = data.get("nama_lengkap")
        if not isinstance(v, str) or not v.strip():
            return None, "nama_lengkap wajib diisi"
        if len(v.strip()) > 100:
            return None, "nama_lengkap maksimal 100 karakter"
        out["nama_lengkap"] = v.strip()
    if buat or "username" in data:
        v = data.get("username")
        if not isinstance(v, str) or not _USERNAME_RE.match(v.strip()):
            return None, "username 3-50 karakter: huruf, angka, titik, garis bawah, atau minus"
        out["username"] = v.strip()
    if buat or "peran" in data:
        v = data.get("peran", "teknisi")
        if v not in PERAN_VALID:
            return None, "peran harus salah satu dari: " + ", ".join(PERAN_VALID)
        out["peran"] = v
    if "no_hp" in data:
        v = data.get("no_hp")
        if v is None or (isinstance(v, str) and not v.strip()):
            out["no_hp"] = None
        elif isinstance(v, str) and _NOHP_RE.match(v.strip()):
            out["no_hp"] = v.strip()
        else:
            return None, "no_hp tidak valid"
    if "id_regu" in data:
        v = data.get("id_regu")
        if v is None or v == "":
            out["id_regu"] = None
        else:
            if isinstance(v, bool):
                return None, "id_regu tidak valid"
            try:
                v = int(v)
            except (TypeError, ValueError):
                return None, "id_regu tidak valid"
            regu = db.session.get(Regu, v)
            if regu is None:
                return None, "Regu tidak ditemukan"
            if not regu.status_aktif:
                return None, "Regu tidak aktif"
            out["id_regu"] = v
    if "status_aktif" in data:
        v = data.get("status_aktif")
        if not isinstance(v, bool):
            return None, "status_aktif harus true atau false"
        out["status_aktif"] = v
    return out, None


@auth_bp.route("/api/pengguna", methods=["GET"])
@role_required("admin")
def daftar_pengguna():
    q = Pengguna.query
    cari = (request.args.get("q") or "").strip()
    if cari:
        like = f"%{cari}%"
        q = q.filter(db.or_(
            Pengguna.nama_lengkap.ilike(like),
            Pengguna.username.ilike(like),
            Pengguna.no_hp.ilike(like),
        ))
    peran = request.args.get("peran")
    if peran:
        if peran not in PERAN_VALID:
            return _err("peran tidak valid")
        q = q.filter(Pengguna.peran == peran)
    status = request.args.get("status", "semua")
    if status == "aktif":
        q = q.filter(Pengguna.status_aktif == True)  # noqa: E712
    elif status == "nonaktif":
        q = q.filter(Pengguna.status_aktif == False)  # noqa: E712
    elif status != "semua":
        return _err("status harus aktif, nonaktif, atau semua")
    id_regu = request.args.get("id_regu")
    if id_regu == "kosong":
        q = q.filter(Pengguna.id_regu.is_(None))
    elif id_regu:
        if not id_regu.isdigit():
            return _err("id_regu tidak valid")
        q = q.filter(Pengguna.id_regu == int(id_regu))

    total    = q.count()
    page     = max(1, request.args.get("page", 1, type=int) or 1)
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int) or 20))
    items = (q.order_by(Pengguna.nama_lengkap.asc(), Pengguna.id_pengguna.asc())
              .offset((page - 1) * per_page).limit(per_page).all())
    peta = _peta_regu()
    return jsonify({
        "success": True,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, -(-total // per_page)),
        },
        "data": [_bentuk_pengguna(p, peta) for p in items],
    })


@auth_bp.route("/api/pengguna/<int:id_pengguna>", methods=["GET"])
@role_required("admin")
def detail_pengguna(id_pengguna):
    target = db.session.get(Pengguna, id_pengguna)
    if target is None:
        return _err("Pengguna tidak ditemukan", 404)
    return jsonify({"success": True, "data": _bentuk_pengguna(target, _peta_regu())})


@auth_bp.route("/api/pengguna", methods=["POST"])
@role_required("admin")
def buat_pengguna():
    data = _body_json()
    if data is None:
        return _err("Body JSON wajib")
    nilai, pesan = _bersihkan_input(data, buat=True)
    if pesan:
        return _err(pesan)
    pesan = _cek_password(data.get("password"))
    if pesan:
        return _err(pesan)
    if Pengguna.query.filter_by(username=nilai["username"]).first():
        return _err("Username sudah dipakai", 409)

    pengguna = Pengguna(
        nama_lengkap=nilai["nama_lengkap"],
        username=nilai["username"],
        password_hash=generate_password_hash(data["password"]),
        peran=nilai["peran"],
        no_hp=nilai.get("no_hp"),
        id_regu=nilai.get("id_regu"),
        status_aktif=nilai.get("status_aktif", True),
    )
    db.session.add(pengguna)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _err("Username sudah dipakai", 409)
    _audit(f"buat akun (peran={pengguna.peran})", pengguna.username)
    return jsonify({"success": True, "data": _bentuk_pengguna(pengguna, _peta_regu())}), 201


@auth_bp.route("/api/pengguna/<int:id_pengguna>", methods=["PUT", "PATCH"])
@role_required("admin")
def ubah_pengguna(id_pengguna):
    target = db.session.get(Pengguna, id_pengguna)
    if target is None:
        return _err("Pengguna tidak ditemukan", 404)
    data = _body_json()
    if data is None:
        return _err("Body JSON wajib")
    if "password" in data:
        return _err("Password diubah lewat endpoint reset-password")
    nilai, pesan = _bersihkan_input(data, buat=False)
    if pesan:
        return _err(pesan)
    if not nilai:
        return _err("Tidak ada field yang diubah")

    diri_sendiri = target.id_pengguna == g.pengguna.id_pengguna
    if diri_sendiri and nilai.get("status_aktif") is False:
        return _err("Tidak bisa menonaktifkan akun sendiri", 409)
    if diri_sendiri and "peran" in nilai and nilai["peran"] != target.peran:
        return _err("Tidak bisa mengubah peran akun sendiri", 409)
    if "username" in nilai and nilai["username"] != target.username:
        bentrok = Pengguna.query.filter(
            Pengguna.username == nilai["username"],
            Pengguna.id_pengguna != target.id_pengguna,
        ).first()
        if bentrok:
            return _err("Username sudah dipakai", 409)

    for kolom, isi in nilai.items():
        setattr(target, kolom, isi)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _err("Username sudah dipakai", 409)
    _audit(f"ubah akun ({', '.join(sorted(nilai))})", target.username)
    return jsonify({"success": True, "data": _bentuk_pengguna(target, _peta_regu())})


@auth_bp.route("/api/pengguna/<int:id_pengguna>/reset-password", methods=["POST"])
@role_required("admin")
def reset_password_pengguna(id_pengguna):
    target = db.session.get(Pengguna, id_pengguna)
    if target is None:
        return _err("Pengguna tidak ditemukan", 404)
    data = _body_json()
    if data is None:
        return _err("Body JSON wajib")
    pesan = _cek_password(data.get("password"))
    if pesan:
        return _err(pesan)
    target.password_hash = generate_password_hash(data["password"])
    db.session.commit()
    _audit("reset password", target.username)
    return jsonify({"success": True, "pesan": "Password berhasil diganti"})


@auth_bp.route("/api/auth/ubah-password", methods=["POST"])
@jwt_required
def ubah_password_sendiri():
    data = _body_json()
    if data is None:
        return _err("Body JSON wajib")
    lama = data.get("password_lama")
    baru = data.get("password_baru")
    if not isinstance(lama, str) or not lama:
        return _err("password_lama wajib diisi")
    pesan = _cek_password(baru)
    if pesan:
        return _err(pesan)
    pengguna = g.pengguna
    if not check_password_hash(pengguna.password_hash, lama):
        return _err("Password lama salah")
    if lama == baru:
        return _err("Password baru harus berbeda dari password lama")
    pengguna.password_hash = generate_password_hash(baru)
    db.session.commit()
    _audit("ubah password sendiri", pengguna.username)
    return jsonify({"success": True, "pesan": "Password berhasil diganti"})
