"""
auth_routes.py — Blueprint autentikasi JWT untuk PIJAR
Endpoint:
  POST /api/auth/login   — return access token
  POST /api/auth/logout  — blacklist token aktif (logout)
  GET  /api/auth/me      — info pengguna dari token
  POST /api/auth/seed    — buat akun admin pertama (sekali pakai, disabled di production)
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Pengguna

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
        "jti":      str(uuid.uuid4()),   # JWT ID unik — dipakai blacklist logout
        "sub":      pengguna.id_pengguna,
        "username": pengguna.username,
        "peran":    pengguna.peran,
        "nama":     pengguna.nama_lengkap,
        "exp":      exp,
    }
    return jwt.encode(payload, secret, algorithm="HS256"), exp


# ------------------------------------------------------------------ #
# Decorator: proteksi endpoint
# ------------------------------------------------------------------ #
def jwt_required(f):
    """Decorator — wajib login. Isi g.user_payload dari token."""
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
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token kadaluarsa, silakan login ulang"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Token tidak valid"}), 401

        # Cek blacklist: token sudah di-logout?
        jti = payload.get("jti")
        if jti and jti in _BLACKLIST:
            return jsonify({"success": False, "error": "Token sudah tidak aktif, silakan login ulang"}), 401

        g.user_payload = payload
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Decorator — batasi akses berdasarkan peran."""
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
