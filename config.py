import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://suryaci1_pju:Kimprasw1l@localhost/suryaci1_pjudb"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Shared hosting: recycle koneksi tiap 5 menit, ping sebelum pakai
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "pool_size": 5,
        "max_overflow": 2,
    }

    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    # CORS
    CORS_ORIGINS = [
        "https://admin.pjujogja.id",
        "https://pjujogja.id",
        "http://localhost:3000",
        "http://localhost:5500",
    ]

    # JWT
    # Fallback ke SECRET_KEY jika JWT_SECRET tidak di-set secara terpisah.
    # Ini memastikan deployment cPanel yang hanya punya SECRET_KEY tetap berfungsi.
    JWT_SECRET = (
        os.getenv("JWT_SECRET")
        or os.getenv("SECRET_KEY", "GANTI_DENGAN_SECRET_PANJANG_DI_ENV")
    )
    JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "12"))

    # Seed key (untuk endpoint /api/auth/seed)
    SEED_SECRET = os.getenv("SEED_SECRET", "GANTI_INI")

    # Bobot prioritas Fase 1
    BOBOT_KATEGORI_JALAN = {
        "Jalan Kota": 3,
        "Jalan Lingkungan": 2,
        "Jalan Lingkungan Kampung": 1,
        "Lainnya": 1,
    }
