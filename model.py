import logging
import time
from datetime import datetime

import pymysql
from flask_sqlalchemy import SQLAlchemy

from config import Config

# Konfigurasi logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Objek SQLAlchemy yang dipakai oleh aplikasi dan migrasi.
db = SQLAlchemy()


class Database:
    """Wrapper sederhana untuk koneksi database menggunakan PyMySQL."""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connection = self._create_connection()

    def _create_connection(self):
        # Pastikan semua konfigurasi database ada sebelum mencoba koneksi.
        if not Config.DB_HOST or not Config.DB_USER or not Config.DB_PASSWORD or not Config.DB_NAME:
            raise ValueError(
                "Konfigurasi database belum lengkap. Isi DB_HOST, DB_USER, DB_PASSWORD, dan DB_NAME di file .env."
            )

        return pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            autocommit=True,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor,
            ssl=Config.DB_SSL_CONFIG,
        )

    def get_connection(self):
        """Mengambil koneksi yang masih aktif atau membuat koneksi baru."""
        if self._connection is None or not getattr(self._connection, "open", False):
            self._connection = self._create_connection()
        return self._connection

    def execute_query(self, query, params=None, fetch=False):
        """Menjalankan query dengan opsi fetch untuk SELECT."""
        start_time = time.time()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            if fetch:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid if cursor.lastrowid else True

            elapsed = time.time() - start_time
            logger.info("Query executed in %.3fs: %s", elapsed, query[:50])
            return result
        except Exception as exc:
            conn.rollback()
            raise exc
        finally:
            cursor.close()


class User(db.Model):
    """Model pengguna untuk sistem portfolio."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="admin")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    skills = db.relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    experiences = db.relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    projects = db.relationship("Project", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Profile(db.Model):
    """Profil data pribadi milik satu user."""

    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    nama_lengkap = db.Column(db.String(150), nullable=True)
    nama_panggilan = db.Column(db.String(100), nullable=True)
    tempat_lahir = db.Column(db.String(100), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(150), nullable=True)
    telepon = db.Column(db.String(50), nullable=True)
    universitas = db.Column(db.String(150), nullable=True)
    fakultas = db.Column(db.String(150), nullable=True)
    prodi = db.Column(db.String(150), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    foto_url = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile {self.nama_lengkap or self.user_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nama_lengkap": self.nama_lengkap,
            "nama_panggilan": self.nama_panggilan,
            "tempat_lahir": self.tempat_lahir,
            "tanggal_lahir": self.tanggal_lahir.isoformat() if self.tanggal_lahir else None,
            "email": self.email,
            "telepon": self.telepon,
            "universitas": self.universitas,
            "fakultas": self.fakultas,
            "prodi": self.prodi,
            "semester": self.semester,
            "alamat": self.alamat,
            "foto_url": self.foto_url,
        }


class Skill(db.Model):
    """Skill yang dimiliki oleh user."""

    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nama_skill = db.Column(db.String(100), nullable=False)
    icon_class = db.Column(db.String(100), nullable=True)

    user = db.relationship("User", back_populates="skills")

    def __repr__(self):
        return f"<Skill {self.nama_skill}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nama_skill": self.nama_skill,
            "icon_class": self.icon_class,
        }


class Experience(db.Model):
    """Riwayat pengalaman kerja atau organisasi."""

    __tablename__ = "experiences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    posisi = db.Column(db.String(150), nullable=False)
    perusahaan = db.Column(db.String(150), nullable=False)
    durasi = db.Column(db.String(100), nullable=True)
    deskripsi = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="experiences")

    def __repr__(self):
        return f"<Experience {self.posisi} at {self.perusahaan}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "posisi": self.posisi,
            "perusahaan": self.perusahaan,
            "durasi": self.durasi,
            "deskripsi": self.deskripsi,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Project(db.Model):
    """Project yang dimiliki oleh user."""

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    judul = db.Column(db.String(150), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    gambar_url = db.Column(db.String(255), nullable=True)
    link_project = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="projects")

    def __repr__(self):
        return f"<Project {self.judul}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "judul": self.judul,
            "deskripsi": self.deskripsi,
            "gambar_url": self.gambar_url,
            "link_project": self.link_project,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Contact(db.Model):
    """Form kontak yang masuk dari website."""

    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subjek = db.Column(db.String(150), nullable=True)
    pesan = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Belum Dibaca")

    def __repr__(self):
        return f"<Contact {self.nama}>"

    def to_dict(self):
        return {
            "id": self.id,
            "nama": self.nama,
            "email": self.email,
            "subjek": self.subjek,
            "pesan": self.pesan,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
        }
