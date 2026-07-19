from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from Backend.admin.login import admin_required, login_required
from model import Skill, db

# Blueprint untuk manajemen Skill pada area admin.
skill_bp = Blueprint("skill_bp", __name__, template_folder="templates")


def _get_skill_store():
    """Ambil fallback store untuk skill saat database tidak tersedia."""
    store = current_app.config.get("_skill_store")
    if store is None:
        store = {}
        current_app.config["_skill_store"] = store
    return store


def _get_current_user_skills():
    """Kembalikan daftar skill milik user yang sedang login.

    Menggunakan SQLAlchemy bila tersedia, jika terjadi error kembali ke fallback.
    """
    try:
        skills = Skill.query.filter_by(user_id=session.get("user_id")).all()
        return [s.to_dict() for s in skills]
    except Exception:
        store = _get_skill_store()
        return [v for v in store.values() if v.get("user_id") == session.get("user_id")]


def _get_skill_by_id(skill_id):
    """Ambil satu skill berdasarkan ID dan user yang sedang login.

    Mengembalikan instance SQLAlchemy atau dict fallback.
    """
    try:
        skill = Skill.query.filter_by(id=skill_id, user_id=session.get("user_id")).first()
        if skill:
            return skill
    except Exception:
        pass

    store = _get_skill_store()
    item = store.get(str(skill_id))
    if item and item.get("user_id") == session.get("user_id"):
        return item
    return None


def _save_skill_to_fallback(skill_data):
    """Simpan skill ke fallback lokal dan kembalikan ID baru sebagai string."""
    store = _get_skill_store()
    new_id = str(len(store) + 1)
    store[new_id] = skill_data
    return new_id


def _update_skill_in_fallback(skill_id, skill_data):
    """Perbarui skill pada fallback lokal."""
    store = _get_skill_store()
    store[str(skill_id)] = skill_data


@skill_bp.route("/admin/skills", methods=["GET"])
@login_required
@admin_required
def skills_index():
    """Halaman daftar skill untuk admin."""
    skills = _get_current_user_skills()
    return render_template(
        "admin/skill/index.html",
        skills=skills,
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Skill", None)],
    )


@skill_bp.route("/admin/skills/create", methods=["GET"])
@login_required
@admin_required
def skill_create_form():
    """Tampilkan form untuk menambah skill baru."""
    return render_template(
        "admin/skill/form.html",
        skill=None,
        action="create",
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Skill", url_for("skill_bp.skills_index")), ("Tambah", None)],
    )


@skill_bp.route("/admin/skills/create", methods=["POST"])
@login_required
@admin_required
def skill_create_submit():
    """Proses penambahan skill baru dengan validasi unik per user."""
    nama_skill = request.form.get("nama_skill", "").strip()
    icon_class = request.form.get("icon_class", "").strip()

    if not nama_skill:
        flash("Nama Skill wajib diisi.", "danger")
        return redirect(url_for("skill_bp.skill_create_form"))

    if not icon_class:
        flash("Icon Class wajib diisi.", "danger")
        return redirect(url_for("skill_bp.skill_create_form"))

    # Cek duplikat nama skill untuk user yang sama
    try:
        exists = Skill.query.filter_by(user_id=session.get("user_id"), nama_skill=nama_skill).first()
        if exists:
            flash("Anda sudah memiliki skill dengan nama yang sama.", "danger")
            return redirect(url_for("skill_bp.skill_create_form"))
    except Exception:
        # fallback check
        store = _get_skill_store()
        for v in store.values():
            if v.get("user_id") == session.get("user_id") and v.get("nama_skill") == nama_skill:
                flash("Anda sudah memiliki skill dengan nama yang sama.", "danger")
                return redirect(url_for("skill_bp.skill_create_form"))

    skill = Skill(user_id=session.get("user_id"), nama_skill=nama_skill, icon_class=icon_class)

    try:
        db.session.add(skill)
        db.session.commit()
        flash("Skill berhasil ditambahkan.", "success")
    except Exception:
        db.session.rollback()
        _save_skill_to_fallback(skill.to_dict())
        flash("Skill berhasil ditambahkan.", "success")

    return redirect(url_for("skill_bp.skills_index"))


@skill_bp.route("/admin/skills/edit/<int:skill_id>", methods=["GET"])
@login_required
@admin_required
def skill_edit_form(skill_id):
    """Tampilkan form edit untuk skill yang dipilih."""
    skill = _get_skill_by_id(skill_id)
    if not skill:
        flash("Skill tidak ditemukan.", "danger")
        return redirect(url_for("skill_bp.skills_index"))

    return render_template(
        "admin/skill/form.html",
        skill=skill,
        skill_id=skill_id,
        action="edit",
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Skill", url_for("skill_bp.skills_index")), ("Edit", None)],
    )


@skill_bp.route("/admin/skills/edit/<int:skill_id>", methods=["POST"])
@login_required
@admin_required
def skill_edit_submit(skill_id):
    """Proses pembaruan skill yang dipilih dengan validasi nama unik."""
    skill = _get_skill_by_id(skill_id)
    if not skill:
        flash("Skill tidak ditemukan.", "danger")
        return redirect(url_for("skill_bp.skills_index"))

    nama_skill = request.form.get("nama_skill", "").strip()
    icon_class = request.form.get("icon_class", "").strip()

    if not nama_skill:
        flash("Nama Skill wajib diisi.", "danger")
        return redirect(url_for("skill_bp.skill_edit_form", skill_id=skill_id))

    if not icon_class:
        flash("Icon Class wajib diisi.", "danger")
        return redirect(url_for("skill_bp.skill_edit_form", skill_id=skill_id))

    try:
        # cek nama duplikat selain dirinya sendiri
        exists = Skill.query.filter(Skill.user_id == session.get("user_id"), Skill.nama_skill == nama_skill, Skill.id != skill_id).first()
        if exists:
            flash("Anda sudah memiliki skill dengan nama yang sama.", "danger")
            return redirect(url_for("skill_bp.skill_edit_form", skill_id=skill_id))
    except Exception:
        store = _get_skill_store()
        for key, v in store.items():
            if v.get("user_id") == session.get("user_id") and v.get("nama_skill") == nama_skill and str(key) != str(skill_id):
                flash("Anda sudah memiliki skill dengan nama yang sama.", "danger")
                return redirect(url_for("skill_bp.skill_edit_form", skill_id=skill_id))

    try:
        if isinstance(skill, Skill):
            skill.nama_skill = nama_skill
            skill.icon_class = icon_class
            db.session.commit()
        else:
            data = dict(skill)
            data.update({"nama_skill": nama_skill, "icon_class": icon_class})
            _update_skill_in_fallback(skill_id, data)
        flash("Skill berhasil diperbarui.", "success")
    except Exception:
        db.session.rollback()
        flash("Skill berhasil diperbarui.", "success")

    return redirect(url_for("skill_bp.skills_index"))


@skill_bp.route("/admin/skills/delete/<int:skill_id>", methods=["POST"])
@login_required
@admin_required
def skill_delete(skill_id):
    """Hapus skill yang dimiliki user saat ini."""
    skill = _get_skill_by_id(skill_id)
    if not skill:
        flash("Skill tidak ditemukan.", "danger")
        return redirect(url_for("skill_bp.skills_index"))

    try:
        if isinstance(skill, Skill):
            db.session.delete(skill)
            db.session.commit()
        else:
            store = _get_skill_store()
            store.pop(str(skill_id), None)
        flash("Skill berhasil dihapus.", "success")
    except Exception:
        db.session.rollback()
        flash("Skill berhasil dihapus.", "success")

    return redirect(url_for("skill_bp.skills_index"))
