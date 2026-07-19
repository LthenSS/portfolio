import resend

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from config import Config
from model import Contact, db
from Backend.admin.login import admin_required, login_required

# Blueprint untuk manajemen Contact pada area admin.
admin_contact_bp = Blueprint("admin_contact_bp", __name__, template_folder="templates")


def _get_contact_store():
    """Ambil fallback store untuk contact saat database tidak tersedia."""
    store = current_app.config.get("_contact_store")
    if store is None:
        store = {}
        current_app.config["_contact_store"] = store
    return store


def _get_current_user_contacts():
    """Kembalikan daftar contact milik user yang sedang login."""
    try:
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        return [c.to_dict() for c in contacts]
    except Exception:
        store = _get_contact_store()
        return sorted(
            [v for v in store.values()],
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )


def _get_contact_by_id(contact_id):
    """Ambil satu contact berdasarkan ID."""
    try:
        contact = Contact.query.filter_by(id=contact_id).first()
        if contact:
            return contact
    except Exception:
        pass

    store = _get_contact_store()
    item = store.get(str(contact_id))
    return item


def _save_contact_to_fallback(contact_data):
    """Simpan contact ke fallback lokal dan kembalikan ID baru sebagai string."""
    store = _get_contact_store()
    new_id = str(len(store) + 1)
    contact_data = dict(contact_data)
    contact_data["id"] = new_id
    store[new_id] = contact_data
    return new_id


def _update_contact_in_fallback(contact_id, contact_data):
    """Perbarui contact pada fallback lokal."""
    store = _get_contact_store()
    store[str(contact_id)] = contact_data


def _delete_contact_in_fallback(contact_id):
    """Hapus contact dari fallback lokal."""
    store = _get_contact_store()
    store.pop(str(contact_id), None)


def _send_contact_email(nama, email, subjek, pesan):
    """Kirim email menggunakan Resend jika konfigurasi tersedia."""
    if not Config.RESEND_API_KEY:
        return False, "Resend belum dikonfigurasi."
    if not Config.RESEND_FROM:
        return False, "RESEND_FROM belum dikonfigurasi."
    if not Config.EMAIL_PENERIMA:
        return False, "EMAIL_PENERIMA belum dikonfigurasi."

    try:
        resend.api_key = Config.RESEND_API_KEY
        from resend import Emails

        Emails.send(
            {
                "from": Config.RESEND_FROM,
                "to": [Config.EMAIL_PENERIMA],
                "subject": f"Pesan Kontak Baru: {subjek}",
                "text": (
                    f"Nama: {nama}\n"
                    f"Email: {email}\n"
                    f"Subjek: {subjek}\n"
                    f"Pesan:\n{pesan}"
                ),
                "html": (
                    f"<p><strong>Nama:</strong> {nama}</p>"
                    f"<p><strong>Email:</strong> {email}</p>"
                    f"<p><strong>Subjek:</strong> {subjek}</p>"
                    f"<p><strong>Pesan:</strong><br>{pesan.replace('\n', '<br>')}</p>"
                ),
            }
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


@admin_contact_bp.route("/admin/contacts", methods=["GET"])
@login_required
@admin_required
def contacts_index():
    """Halaman daftar contact admin."""
    contacts = _get_current_user_contacts()
    return render_template(
        "admin/contact/index.html",
        contacts=contacts,
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Contact", None)],
    )


@admin_contact_bp.route("/admin/contacts/<int:contact_id>", methods=["GET"])
@login_required
@admin_required
def contact_detail(contact_id):
    """Tampilkan detail contact dan tandai sebagai sudah dibaca otomatis."""
    contact = _get_contact_by_id(contact_id)
    if not contact:
        flash("Contact tidak ditemukan.", "danger")
        return redirect(url_for("admin_contact_bp.contacts_index"))

    if isinstance(contact, Contact):
        if contact.status != "Sudah Dibaca":
            contact.status = "Sudah Dibaca"
            db.session.commit()
    else:
        if contact.get("status") != "Sudah Dibaca":
            data = dict(contact)
            data["status"] = "Sudah Dibaca"
            _update_contact_in_fallback(contact_id, data)
            contact = data

    return render_template(
        "admin/contact/detail.html",
        contact=contact,
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Contact", url_for("admin_contact_bp.contacts_index")), ("Detail", None)],
    )


@admin_contact_bp.route("/admin/contacts/delete/<int:contact_id>", methods=["POST"])
@login_required
@admin_required
def contact_delete(contact_id):
    """Hapus contact yang dipilih oleh admin."""
    contact = _get_contact_by_id(contact_id)
    if not contact:
        flash("Contact tidak ditemukan.", "danger")
        return redirect(url_for("admin_contact_bp.contacts_index"))

    try:
        if isinstance(contact, Contact):
            db.session.delete(contact)
            db.session.commit()
        else:
            _delete_contact_in_fallback(contact_id)
        flash("Pesan berhasil dihapus.", "success")
    except Exception:
        db.session.rollback()
        flash("Pesan berhasil dihapus.", "success")

    return redirect(url_for("admin_contact_bp.contacts_index"))


@admin_contact_bp.route("/admin/contacts/read/<int:contact_id>", methods=["POST"])
@login_required
@admin_required
def contact_mark_read(contact_id):
    """Tandai contact sebagai sudah dibaca dari daftar admin."""
    contact = _get_contact_by_id(contact_id)
    if not contact:
        flash("Contact tidak ditemukan.", "danger")
        return redirect(url_for("admin_contact_bp.contacts_index"))

    try:
        if isinstance(contact, Contact):
            contact.status = "Sudah Dibaca"
            db.session.commit()
        else:
            data = dict(contact)
            data["status"] = "Sudah Dibaca"
            _update_contact_in_fallback(contact_id, data)
        flash("Status berhasil diperbarui.", "success")
    except Exception:
        db.session.rollback()
        flash("Status berhasil diperbarui.", "success")

    return redirect(url_for("admin_contact_bp.contacts_index"))
