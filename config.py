import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    DB_USER = os.environ.get("DB_USER", "pjujogja_user")
    DB_PASS = os.environ.get("DB_PASS", "CHANGE_ME")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME", "pjujogja_db")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    SECRET_KEY = os.environ.get("SECRET_KEY", "ganti-dengan-secret-key-acak")

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    CORS_ORIGINS = [
        "https://admin.pjujogja.id",
        "https://pjujogja.id",
        "https://pins.pjujogja.id",
    ]

    # ------------------------------------------------------------------
    # Kategori jalan Perwal Kota Yogyakarta No. 50/2022, ditambah kategori
    # "Lainnya" untuk penerangan non-jalan sesuai Pasal 1 ayat 1 & Pasal 13
    # (taman, makam, sorot sungai, hias/budaya).
    #   - Jalan Kota (tiang >= 7.000 mm)               -> bobot 3
    #   - Jalan Lingkungan (tiang <= 7.000 mm)          -> bobot 2
    #   - Jalan Lingkungan Kampung (tiang <= 4.000 mm)  -> bobot 1
    #   - Lainnya (Taman/Makam/Sorot Sungai/Hias-Budaya) -> bobot 1
    # ------------------------------------------------------------------
    BOBOT_KATEGORI_JALAN = {
        "Jalan Kota": 3,
        "Jalan Lingkungan": 2,
        "Jalan Lingkungan Kampung": 1,
        "Lainnya": 1,
    }

    # Sub-kategori khusus untuk kategori "Lainnya" (Pasal 1 & 13)
    SUB_KATEGORI_LAINNYA = ("Taman", "Makam", "Sorot Sungai", "Hias/Budaya")
