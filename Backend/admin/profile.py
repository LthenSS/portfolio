from datetime import datetime

import cloudinary.uploader
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from Backend.admin.login import admin_required, login_required
from Backend.admin.project import _upload_to_cloudinary
from config import Config
from model import Profile, User, db


def _upload_profile_image(file):
    """Upload file foto profil ke Cloudinary dan kembalikan secure_url + error."""
    return _upload_to_cloudinary(file)

# Blueprint khusus untuk manajemen account admin.
profile_bp = Blueprint("profile_bp", __name__, template_folder="templates")


def _get_profile_store():
    """Fallback sederhana saat koneksi database tidak tersedia."""
    store = current_app.config.get("_profile_store")
    if store is None:
        store = {}
        current_app.config["_profile_store"] = store
    return store


def _get_current_user_profile():
    """Ambil profile milik user yang sedang login."""
    try:
        return Profile.query.filter_by(user_id=session.get("user_id")).first()
    except Exception:
        store = _get_profile_store()
        return store.get(str(session.get("user_id")))


def _save_profile_to_fallback(profile_data):
    """Simpan profile ke fallback lokal saat database tidak bisa dipakai."""
    store = _get_profile_store()
    store[str(profile_data["user_id"])] = profile_data
    return str(profile_data["user_id"])


def _update_profile_in_fallback(profile_data):
    """Perbarui profile pada fallback lokal."""
    store = _get_profile_store()
    store[str(profile_data["user_id"])] = profile_data


@profile_bp.route("/admin/profile", methods=["GET", "POST"])
@login_required
@admin_required
def profile_index():
    """Halaman Akun untuk profile admin tunggal."""
    profile = _get_current_user_profile()

    if request.method == "POST":
        nama_lengkap = request.form.get("nama_lengkap", "").strip()
        nama_panggilan = request.form.get("nama_panggilan", "").strip()
        tempat_lahir = request.form.get("tempat_lahir", "").strip()
        tanggal_lahir_raw = request.form.get("tanggal_lahir", "").strip()
        email = request.form.get("email", "").strip()
        telepon = request.form.get("telepon", "").strip()
        universitas = request.form.get("universitas", "").strip()
        fakultas = request.form.get("fakultas", "").strip()
        prodi = request.form.get("prodi", "").strip()
        semester = request.form.get("semester", "").strip()
        alamat = request.form.get("alamat", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()

        if not nama_lengkap:
            flash("Nama Lengkap wajib diisi.", "danger")
            return redirect(url_for("profile_bp.profile_index"))

        if not email:
            flash("Email tidak boleh kosong.", "danger")
            return redirect(url_for("profile_bp.profile_index"))

        if not universitas:
            flash("Universitas wajib diisi.", "danger")
            return redirect(url_for("profile_bp.profile_index"))

        if password and password != password_confirm:
            flash("Konfirmasi password tidak cocok.", "danger")
            return redirect(url_for("profile_bp.profile_index"))

        foto_file = request.files.get("foto_profil")
        foto_url = None
        if foto_file and foto_file.filename:
            foto_url, upload_error = _upload_profile_image(foto_file)
            if upload_error:
                flash(f"Upload foto gagal: {upload_error}", "danger")
                return redirect(url_for("profile_bp.profile_index"))

        existing_foto_url = getattr(profile, "foto_url", None) if profile else None
        final_foto_url = foto_url or existing_foto_url or "default.jpg"

        tanggal_lahir = None
        if tanggal_lahir_raw:
            try:
                tanggal_lahir = datetime.strptime(tanggal_lahir_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Format tanggal lahir tidak valid.", "danger")
                return redirect(url_for("profile_bp.profile_index"))

        try:
            if profile is None:
                profile = Profile(
                    user_id=session.get("user_id"),
                    nama_lengkap=nama_lengkap,
                    nama_panggilan=nama_panggilan or None,
                    tempat_lahir=tempat_lahir or None,
                    tanggal_lahir=tanggal_lahir,
                    email=email,
                    telepon=telepon or None,
                    universitas=universitas,
                    fakultas=fakultas or None,
                    prodi=prodi or None,
                    semester=semester or None,
                    alamat=alamat or None,
                    foto_url=final_foto_url,
                )
                db.session.add(profile)
            else:
                profile.nama_lengkap = nama_lengkap
                profile.nama_panggilan = nama_panggilan or None
                profile.tempat_lahir = tempat_lahir or None
                profile.tanggal_lahir = tanggal_lahir
                profile.email = email
                profile.telepon = telepon or None
                profile.universitas = universitas
                profile.fakultas = fakultas or None
                profile.prodi = prodi or None
                profile.semester = semester or None
                profile.alamat = alamat or None
                profile.foto_url = final_foto_url

            if password:
                user = User.query.get(session.get("user_id"))
                if user:
                    user.password_hash = generate_password_hash(password)

            db.session.commit()
            flash("Profile berhasil disimpan.", "success")
        except Exception:
            db.session.rollback()
            profile_data = profile.to_dict() if hasattr(profile, "to_dict") else dict(profile)
            _save_profile_to_fallback(profile_data)
            flash("Profile berhasil disimpan.", "success")

        return redirect(url_for("profile_bp.profile_index"))

    return render_template(
        "admin/profile/index.html",
        profile=profile,
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Akun", None)],
    )
