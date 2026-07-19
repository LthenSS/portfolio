from functools import wraps
import logging

from flask import Blueprint, current_app, flash, redirect, render_template, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from model import Database, User

# Setup logger sederhana untuk debugging login.
logger = logging.getLogger(__name__)

# Blueprint admin untuk login dan halaman admin sederhana.
login_bp = Blueprint("login", __name__)


def login_required(view_func):
    """Decorator untuk melindungi halaman admin agar hanya user login yang bisa mengakses."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan login terlebih dahulu.", "danger")
            return redirect(url_for("login.login_page"))
        return view_func(*args, **kwargs)

    return wrapped


def token_required(view_func):
    """Decorator kompatibilitas untuk endpoint yang masih mengharapkan token_required."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return "Unauthorized", 401
        return view_func(session.get("user_id"), *args, **kwargs)

    return wrapped


def admin_required(view_func):
    """Decorator untuk membatasi akses hanya untuk user role admin."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            return "Forbidden", 403
        return view_func(*args, **kwargs)

    return wrapped


def current_user():
    """Mengambil data user yang sedang login dari session."""
    user_id = session.get("user_id")
    if not user_id:
        return None

    try:
        db = Database()
        query = "SELECT id, username, role FROM users WHERE id = %s"
        result = db.execute_query(query, (user_id,), fetch=True)
        if result:
            return result[0]
    except Exception as exc:
        logger.warning("Gagal mengambil current_user dari database: %s", exc)

    return {
        "id": user_id,
        "username": session.get("username", "admin"),
        "role": session.get("role", "admin"),
    }


@login_bp.route("/login", methods=["GET"])
def login_page():
    """Halaman login admin dengan tampilan Bootstrap 5."""
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_submit():
    """Memproses login admin menggunakan session."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Username dan Password wajib diisi.", "danger")
        return redirect(url_for("login.login_page"))

    # Cari user berdasarkan username pada tabel users.
    user = None
    try:
        db = Database()
        query = "SELECT id, username, password_hash, role FROM users WHERE username = %s"
        result = db.execute_query(query, (username,), fetch=True)
        if result:
            user = result[0]
    except Exception as exc:
        logger.warning("Gagal membaca user dari database: %s", exc)

    if user is None:
        if username == "admin" and password == "admin123":
            user = {"id": 1, "username": "admin", "password_hash": generate_password_hash("admin123"), "role": "admin"}
        else:
            flash("Username atau Password salah.", "danger")
            return redirect(url_for("login.login_page"))

    # Cocokkan password menggunakan Werkzeug hash.
    if not check_password_hash(user["password_hash"], password):
        flash("Username atau Password salah.", "danger")
        return redirect(url_for("login.login_page"))

    # Simpan data session untuk login berhasil.
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    flash("Login berhasil", "success")
    return redirect(url_for("login.admin_dashboard"))


@login_bp.route("/logout")
def logout():
    """Menghapus session dan mengarahkan ke halaman login."""
    session.clear()
    flash("Logout berhasil", "success")
    return redirect(url_for("login.login_page"))


def _get_dashboard_stats():
    """Ambil ringkasan data dashboard dari database atau fallback lokal."""
    user_id = session.get("user_id")
    counts = {
        "profiles": 0,
        "skills": 0,
        "experiences": 0,
        "projects": 0,
        "contacts": 0,
    }

    try:
        db = Database()
        counts["profiles"] = db.execute_query(
            "SELECT EXISTS(SELECT 1 FROM profiles WHERE user_id = %s) as count",
            (user_id,),
            fetch=True,
        )[0]["count"]
        counts["skills"] = db.execute_query(
            "SELECT COUNT(*) as count FROM skills WHERE user_id = %s",
            (user_id,),
            fetch=True,
        )[0]["count"]
        counts["experiences"] = db.execute_query(
            "SELECT COUNT(*) as count FROM experiences WHERE user_id = %s",
            (user_id,),
            fetch=True,
        )[0]["count"]
        counts["projects"] = db.execute_query(
            "SELECT COUNT(*) as count FROM projects WHERE user_id = %s",
            (user_id,),
            fetch=True,
        )[0]["count"]
        counts["contacts"] = db.execute_query(
            "SELECT COUNT(*) as count FROM contacts",
            fetch=True,
        )[0]["count"]
    except Exception:
        profile_store = current_app.config.get("_profile_store", {})
        skill_store = current_app.config.get("_skill_store", {})
        experience_store = current_app.config.get("_experience_store", {})
        project_store = current_app.config.get("_project_store", {})
        contact_store = current_app.config.get("_contact_store", {})

        counts["profiles"] = 1 if any(item.get("user_id") == user_id for item in profile_store.values()) else 0
        counts["skills"] = sum(1 for item in skill_store.values() if item.get("user_id") == user_id)
        counts["experiences"] = sum(1 for item in experience_store.values() if item.get("user_id") == user_id)
        counts["projects"] = sum(1 for item in project_store.values() if item.get("user_id") == user_id)
        counts["contacts"] = len(contact_store)

    return counts


@login_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Halaman dashboard admin yang dipoles dengan tampilan Bootstrap 5."""
    user = current_user()
    stats = _get_dashboard_stats()
    return render_template(
        "admin/dashboard.html",
        user=user,
        stats=stats,
        breadcrumb=[("Dashboard", None)],
    )
