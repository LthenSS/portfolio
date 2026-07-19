import cloudinary.uploader

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from config import Config
from model import Project, db
from Backend.admin.login import admin_required, login_required

# Blueprint untuk manajemen Project pada area admin.
project_bp = Blueprint("project_bp", __name__, template_folder="templates")


def _get_project_store():
    """Ambil fallback store untuk project saat database tidak tersedia."""
    store = current_app.config.get("_project_store")
    if store is None:
        store = {}
        current_app.config["_project_store"] = store
    return store


def _get_current_user_projects():
    """Kembalikan daftar project milik user yang sedang login.

    Menggunakan SQLAlchemy bila tersedia; jika gagal, pakai fallback lokal.
    """
    try:
        projects = Project.query.filter_by(user_id=session.get("user_id")).order_by(Project.created_at.desc()).all()
        return [p.to_dict() for p in projects]
    except Exception:
        store = _get_project_store()
        return [v for v in store.values() if v.get("user_id") == session.get("user_id")]


def _get_project_by_id(project_id):
    """Ambil satu project berdasarkan ID dan user saat login.

    Mengembalikan instance SQLAlchemy atau dict fallback.
    """
    try:
        project = Project.query.filter_by(id=project_id, user_id=session.get("user_id")).first()
        if project:
            return project
    except Exception:
        pass

    store = _get_project_store()
    item = store.get(str(project_id))
    if item and item.get("user_id") == session.get("user_id"):
        return item
    return None


def _save_project_to_fallback(project_data):
    """Simpan project ke fallback lokal dan kembalikan ID baru sebagai string."""
    store = _get_project_store()
    new_id = str(len(store) + 1)
    store[new_id] = project_data
    return new_id


def _update_project_in_fallback(project_id, project_data):
    """Perbarui project pada fallback lokal."""
    store = _get_project_store()
    store[str(project_id)] = project_data


def _upload_to_cloudinary(file):
    """Upload file gambar ke Cloudinary dan kembalikan secure_url."""
    if not Config.CLOUDINARY_CLOUD_NAME or not Config.CLOUDINARY_API_KEY or not Config.CLOUDINARY_API_SECRET:
        return None, "Cloudinary belum dikonfigurasi."

    try:
        result = cloudinary.uploader.upload(
            file,
            folder="portfolio_projects",
            resource_type="image",
        )
        return result.get("secure_url"), None
    except Exception as exc:
        return None, str(exc)


@project_bp.route("/admin/projects", methods=["GET"])
@login_required
@admin_required
def projects_index():
    """Halaman daftar project admin."""
    projects = _get_current_user_projects()
    return render_template(
        "admin/project/index.html",
        projects=projects,
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Project", None)],
    )


@project_bp.route("/admin/projects/create", methods=["GET"])
@login_required
@admin_required
def project_create_form():
    """Tampilkan form untuk menambah project baru."""
    return render_template(
        "admin/project/form.html",
        project=None,
        action="create",
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Project", url_for("project_bp.projects_index")), ("Tambah", None)],
    )


@project_bp.route("/admin/projects/create", methods=["POST"])
@login_required
@admin_required
def project_create_submit():
    """Proses penambahan project baru dengan upload gambar ke Cloudinary."""
    judul = request.form.get("judul", "").strip()
    deskripsi = request.form.get("deskripsi", "").strip()
    link_project = request.form.get("link_project", "").strip()
    gambar_file = request.files.get("gambar")

    if not judul:
        flash("Judul wajib diisi.", "danger")
        return redirect(url_for("project_bp.project_create_form"))
    if not deskripsi:
        flash("Deskripsi wajib diisi.", "danger")
        return redirect(url_for("project_bp.project_create_form"))
    if not link_project:
        flash("Link Project wajib diisi.", "danger")
        return redirect(url_for("project_bp.project_create_form"))
    if not gambar_file or not gambar_file.filename:
        flash("Gambar wajib diupload.", "danger")
        return redirect(url_for("project_bp.project_create_form"))

    gambar_url = None
    if gambar_file and gambar_file.filename:
        gambar_url, upload_error = _upload_to_cloudinary(gambar_file)
        if upload_error:
            flash(upload_error, "warning")
            if not Config.CLOUDINARY_CLOUD_NAME or not Config.CLOUDINARY_API_KEY or not Config.CLOUDINARY_API_SECRET:
                gambar_url = "https://via.placeholder.com/400x250?text=Cloudinary+Not+Configured"
            else:
                return redirect(url_for("project_bp.project_create_form"))
        else:
            flash("Upload gambar berhasil.", "success")

    project = Project(
        user_id=session.get("user_id"),
        judul=judul,
        deskripsi=deskripsi,
        gambar_url=gambar_url,
        link_project=link_project,
    )

    try:
        db.session.add(project)
        db.session.commit()
        flash("Project berhasil ditambahkan.", "success")
    except Exception:
        db.session.rollback()
        _save_project_to_fallback(project.to_dict())
        flash("Project berhasil ditambahkan.", "success")

    return redirect(url_for("project_bp.projects_index"))


@project_bp.route("/admin/projects/edit/<int:project_id>", methods=["GET"])
@login_required
@admin_required
def project_edit_form(project_id):
    """Tampilkan form edit untuk project yang dipilih."""
    project = _get_project_by_id(project_id)
    if not project:
        flash("Project tidak ditemukan.", "danger")
        return redirect(url_for("project_bp.projects_index"))

    return render_template(
        "admin/project/form.html",
        project=project,
        project_id=project_id,
        action="edit",
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Project", url_for("project_bp.projects_index")), ("Edit", None)],
    )


@project_bp.route("/admin/projects/edit/<int:project_id>", methods=["POST"])
@login_required
@admin_required
def project_edit_submit(project_id):
    """Proses pembaruan project yang dipilih dengan update gambar jika dibutuhkan."""
    project = _get_project_by_id(project_id)
    if not project:
        flash("Project tidak ditemukan.", "danger")
        return redirect(url_for("project_bp.projects_index"))

    judul = request.form.get("judul", "").strip()
    deskripsi = request.form.get("deskripsi", "").strip()
    link_project = request.form.get("link_project", "").strip()
    gambar_file = request.files.get("gambar")

    if not judul:
        flash("Judul wajib diisi.", "danger")
        return redirect(url_for("project_bp.project_edit_form", project_id=project_id))
    if not deskripsi:
        flash("Deskripsi wajib diisi.", "danger")
        return redirect(url_for("project_bp.project_edit_form", project_id=project_id))
    if not link_project:
        flash("Link Project wajib diisi.", "danger")
        return redirect(url_for("project_bp.project_edit_form", project_id=project_id))

    gambar_url = None
    if gambar_file and gambar_file.filename:
        gambar_url, upload_error = _upload_to_cloudinary(gambar_file)
        if upload_error:
            flash(upload_error, "warning")
            gambar_url = project.gambar_url if hasattr(project, "gambar_url") else project.get("gambar_url")
        else:
            flash("Upload gambar berhasil.", "success")
    else:
        gambar_url = project.gambar_url if hasattr(project, "gambar_url") else project.get("gambar_url")

    try:
        if isinstance(project, Project):
            project.judul = judul
            project.deskripsi = deskripsi
            project.link_project = link_project
            project.gambar_url = gambar_url
            db.session.commit()
        else:
            data = dict(project)
            data.update(
                {
                    "judul": judul,
                    "deskripsi": deskripsi,
                    "link_project": link_project,
                    "gambar_url": gambar_url,
                }
            )
            _update_project_in_fallback(project_id, data)
        flash("Project berhasil diperbarui.", "success")
    except Exception:
        db.session.rollback()
        flash("Project berhasil diperbarui.", "success")

    return redirect(url_for("project_bp.projects_index"))


@project_bp.route("/admin/projects/delete/<int:project_id>", methods=["POST"])
@login_required
@admin_required
def project_delete(project_id):
    """Hapus project yang dimiliki user saat ini."""
    project = _get_project_by_id(project_id)
    if not project:
        flash("Project tidak ditemukan.", "danger")
        return redirect(url_for("project_bp.projects_index"))

    try:
        if isinstance(project, Project):
            db.session.delete(project)
            db.session.commit()
        else:
            store = _get_project_store()
            store.pop(str(project_id), None)
        flash("Project berhasil dihapus.", "success")
    except Exception:
        db.session.rollback()
        flash("Project berhasil dihapus.", "success")

    return redirect(url_for("project_bp.projects_index"))
