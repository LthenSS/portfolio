import os
import sys

# Ensure the project root is on sys.path so `Backend.*` imports work in serverless
# runtimes like Vercel, where the current working directory may not be the project root.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import cloudinary
import pymysql
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate

from config import Config
from model import db

# Import blueprints yang sudah ada.
from Backend.admin.dashboard import dashboard_bp
from Backend.admin.experience import experience_api_bp, experience_bp
from Backend.admin.login import login_bp
from Backend.admin.profile import profile_bp
from Backend.admin.profiles import profiles_bp
from Backend.admin.project import project_bp
from Backend.admin.projects import projects_bp
from Backend.admin.skills import skills_bp
from Backend.admin.skill import skill_bp
from Backend.admin.upload import upload_bp
from Backend.admin.contact import admin_contact_bp
from Backend.public.contact import public_contact_bp
from Backend.public.portfolio import public_portfolio_bp
from Backend.utama.utama import utama_bp

# Inisialisasi ekstensi Flask.
migrate = Migrate()


def check_database_connection():
    """Mengecek koneksi database saat aplikasi dijalankan."""
    if not Config.DB_HOST or not Config.DB_USER or not Config.DB_PASSWORD or not Config.DB_NAME:
        print("Konfigurasi database belum lengkap. Isi DB_HOST, DB_USER, DB_PASSWORD, dan DB_NAME di file .env.")
        return False

    connection = None
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            autocommit=True,
            connect_timeout=10,
            ssl=Config.DB_SSL_CONFIG,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Koneksi Database Berhasil")
        return True
    except Exception as exc:
        print(f"Gagal terhubung ke database: {exc}")
        return False
    finally:
        if connection is not None:
            connection.close()


def configure_services():
    """Menginisialisasi Cloudinary, Resend, dan pengecekan database."""
    # Cloudinary siap digunakan jika semua konfigurasi ada.
    if Config.CLOUDINARY_CLOUD_NAME and Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET:
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET,
        )
        print("Cloudinary siap digunakan")
    else:
        print("Cloudinary belum dikonfigurasi. Isi variabel terkait di file .env.")

    # Resend siap digunakan jika API key tersedia.
    if Config.RESEND_API_KEY:
        import resend

        resend.api_key = Config.RESEND_API_KEY
        print("Resend siap digunakan")
    else:
        print("Resend API Key belum dikonfigurasi. Isi RESEND_API_KEY di file .env.")

    check_database_connection()


def create_app():
    # Template folder menunjuk ke root project agar index.html bisa diakses.
    app = Flask(
        __name__,
        static_folder="Frontend",
        template_folder="templates",
    )

    # Konfigurasi aplikasi diambil dari objek Config.
    app.config.from_object(Config)

    # Inisialisasi ekstensi Flask.
    db.init_app(app)
    migrate.init_app(app, db)

    # Enable CORS untuk kebutuhan development.
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register blueprints.
    app.register_blueprint(login_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(skill_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(admin_contact_bp)
    app.register_blueprint(public_contact_bp)
    app.register_blueprint(public_portfolio_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(profiles_bp, url_prefix="/api")
    app.register_blueprint(experience_api_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(skills_bp, url_prefix="/api")
    app.register_blueprint(experience_bp)
    app.register_blueprint(utama_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")

    @app.route("/index.html")
    def index_file():
        if os.path.exists(os.path.join(app.root_path, "index.html")):
            return send_from_directory(app.root_path, "index.html")
        if os.path.exists(os.path.join(app.root_path, "Frontend", "index.html")):
            return send_from_directory(os.path.join(app.root_path, "Frontend"), "index.html")
        return "Error: index.html not found", 404

    @app.route("/admin/<path:filename>")
    def admin_pages(filename):
        return send_from_directory(os.path.join(app.root_path, "Frontend", "admin"), filename)

    @app.route("/profil/<path:filename>")
    def profil_pages(filename):
        return send_from_directory(os.path.join(app.root_path, "Frontend", "profil"), filename)

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(app.root_path, "favicon.ico", mimetype="image/vnd.microsoft.icon")

    # Error handler dasar.
    @app.errorhandler(404)
    def not_found(error):
        if request.accept_mimetypes.best == "text/html":
            return send_from_directory(app.root_path, "index.html")
        return jsonify({"error": "Route tidak ditemukan"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Terjadi kesalahan pada server"}), 500

    # Jalankan pengecekan layanan saat aplikasi dibuat.
    configure_services()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)