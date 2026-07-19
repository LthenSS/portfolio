import os
from pathlib import Path
from urllib.parse import quote_plus

import certifi
from dotenv import load_dotenv

# Muat konfigurasi dari file .env di root project.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def build_mysql_ssl_config(ca_path=None):
    """Bangun konfigurasi SSL yang aman untuk koneksi TiDB Cloud."""
    resolved_ca_path = (ca_path or os.getenv("DB_CA_PATH", "") or "").strip()
    if resolved_ca_path:
        return {"ca": resolved_ca_path}
    return {"ca": certifi.where()}


class Config:
    # Konfigurasi dasar Flask.
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # Konfigurasi database TiDB Cloud melalui .env.
    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = int(os.getenv("DB_PORT", "4000") or 4000)
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "")
    DB_CA_PATH = os.getenv("DB_CA_PATH", "").strip()
    ssl_ca = DB_CA_PATH

    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
    DB_SSL_CONFIG = build_mysql_ssl_config(ssl_ca)
    DB_SSL_CA = DB_SSL_CONFIG["ca"]

    MYSQL_CONFIG = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
        "ssl": DB_SSL_CONFIG,
    }

    # SQLAlchemy siap digunakan untuk koneksi MySQL + PyMySQL.
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        if DB_HOST and DB_USER and DB_PASSWORD and DB_NAME
        else "sqlite:///:memory:"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": DB_SSL_CONFIG,
        }
    }

    # Konfigurasi Cloudinary dari .env.
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    # Konfigurasi Resend dari .env.
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM = os.getenv("RESEND_FROM", "")
    EMAIL_PENERIMA = os.getenv("EMAIL_PENERIMA", "")