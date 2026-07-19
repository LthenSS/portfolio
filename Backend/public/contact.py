from flask import Blueprint, flash, redirect, render_template, request, url_for

from Backend.admin.contact import _send_contact_email, _save_contact_to_fallback
from model import Contact, db

# Blueprint public untuk halaman contact website.
public_contact_bp = Blueprint("public_contact_bp", __name__, template_folder="templates")


@public_contact_bp.route("/contact", methods=["GET"])
def contact_form():
    """Tampilkan halaman form contact untuk pengunjung."""
    return render_template("public/contact/form.html")


@public_contact_bp.route("/contact", methods=["POST"])
def contact_submit():
    """Proses penyimpanan contact dan pengiriman email Resend."""
    nama = request.form.get("nama", "").strip()
    email = request.form.get("email", "").strip()
    subjek = request.form.get("subjek", "").strip()
    pesan = request.form.get("pesan", "").strip()

    if not nama or not email or not subjek or not pesan:
        flash("Semua field wajib diisi.", "danger")
        return redirect(url_for("public_contact_bp.contact_form"))

    contact = Contact(nama=nama, email=email, subjek=subjek, pesan=pesan)

    try:
        db.session.add(contact)
        db.session.commit()
        flash("Pesan berhasil dikirim.", "success")
    except Exception:
        db.session.rollback()
        _save_contact_to_fallback(contact.to_dict())
        flash("Pesan berhasil dikirim.", "success")

    sent, error = _send_contact_email(nama, email, subjek, pesan)
    if not sent:
        flash(error or "Resend belum dikonfigurasi.", "warning")
    else:
        flash("Email berhasil dikirim.", "success")

    return redirect(url_for("public_contact_bp.contact_form"))
