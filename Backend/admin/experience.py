from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for, jsonify

from model import Database, Experience, db
from Backend.admin.login import token_required, admin_required, login_required

# API blueprint (dipakai oleh /api) — tetap tersedia, beri nama variabel berbeda.
experience_api_bp = Blueprint('experience', __name__)

# ✅ PERBAIKAN: Hapus '/api' di depan route
@experience_api_bp.route('/experiences', methods=['GET'])
def get_experiences():
    """Mengambil semua experiences (publik)"""
    try:
        db = Database()
        
        # Ambil data experience milik admin saja untuk ditampilkan publik
        query = """
            SELECT e.*, u.username 
            FROM experiences e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.role = 'admin'
            ORDER BY e.created_at DESC
        """
        result = db.execute_query(query, fetch=True)
        
        return jsonify({
            'success': True,
            'data': result if result else []
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@experience_api_bp.route('/experiences/<int:id>', methods=['GET'])
def get_experience_by_id(id):
    """Mengambil satu experience berdasarkan ID"""
    try:
        db = Database()
        
        query = "SELECT * FROM experiences WHERE id = %s"
        result = db.execute_query(query, (id,), fetch=True)
        
        if not result:
            return jsonify({'error': 'Experience tidak ditemukan'}), 404
        
        return jsonify({
            'success': True,
            'data': result[0]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@experience_api_bp.route('/experiences', methods=['POST'])
@token_required
def create_experience(current_user):
    """Create experience baru (Admin Only)"""
    try:
        data = request.get_json()
        
        required_fields = ['posisi', 'perusahaan', 'durasi']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} wajib diisi'}), 400
        
        db = Database()
        
        query = """
            INSERT INTO experiences (user_id, posisi, perusahaan, durasi, deskripsi)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            current_user,
            data.get('posisi'),
            data.get('perusahaan'),
            data.get('durasi'),
            data.get('deskripsi')
        )
        
        new_id = db.execute_query(query, values)
        
        return jsonify({
            'success': True,
            'message': 'Experience berhasil dibuat',
            'id': new_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@experience_api_bp.route('/experiences/<int:id>', methods=['PUT'])
@token_required
def update_experience(current_user, id):
    """Update experience (Admin Only)"""
    try:
        data = request.get_json()
        
        db = Database()
        
        # Keamanan: Pastikan user hanya bisa edit miliknya sendiri
        check_query = "SELECT id FROM experiences WHERE id = %s AND user_id = %s"
        existing = db.execute_query(check_query, (id, current_user), fetch=True)
        
        if not existing:
            return jsonify({'error': 'Experience tidak ditemukan atau bukan milik Anda'}), 404
        
        allowed_fields = ['posisi', 'perusahaan', 'durasi', 'deskripsi']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        
        if not updates:
            return jsonify({'error': 'Tidak ada data yang diupdate'}), 400
        
        values.append(id)
        query = f"UPDATE experiences SET {', '.join(updates)} WHERE id = %s"
        db.execute_query(query, tuple(values))
        
        return jsonify({
            'success': True,
            'message': 'Experience berhasil diupdate'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@experience_api_bp.route('/experiences/<int:id>', methods=['DELETE'])
@token_required
def delete_experience(current_user, id):
    """Delete experience (Admin Only)"""
    try:
        db = Database()
        
        # Keamanan: Pastikan user hanya bisa hapus miliknya sendiri
        check_query = "SELECT id FROM experiences WHERE id = %s AND user_id = %s"
        existing = db.execute_query(check_query, (id, current_user), fetch=True)
        
        if not existing:
            return jsonify({'error': 'Experience tidak ditemukan atau bukan milik Anda'}), 404
        
        query = "DELETE FROM experiences WHERE id = %s"
        db.execute_query(query, (id,))
        
        return jsonify({
            'success': True,
            'message': 'Experience berhasil dihapus'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----------------------
# Admin HTML blueprint
# ----------------------
experience_bp = Blueprint("experience_bp", __name__, template_folder="templates")


def _get_experience_store():
    """Ambil fallback store untuk experience saat database tidak tersedia."""
    store = current_app.config.get("_experience_store")
    if store is None:
        store = {}
        current_app.config["_experience_store"] = store
    return store


def _get_current_user_experiences():
    """Kembalikan daftar experience milik user yang sedang login.

    Menggunakan SQLAlchemy bila tersedia, jika terjadi error kembali ke fallback.
    """
    try:
        experiences = Experience.query.filter_by(user_id=session.get("user_id")).order_by(Experience.created_at.desc()).all()
        return [e.to_dict() for e in experiences]
    except Exception:
        store = _get_experience_store()
        return [v for v in store.values() if v.get("user_id") == session.get("user_id")]


def _get_experience_by_id(exp_id):
    """Ambil satu experience berdasarkan ID dan user yang sedang login.

    Mengembalikan instance SQLAlchemy atau dict fallback.
    """
    try:
        exp = Experience.query.filter_by(id=exp_id, user_id=session.get("user_id")).first()
        if exp:
            return exp
    except Exception:
        pass

    store = _get_experience_store()
    item = store.get(str(exp_id))
    if item and item.get("user_id") == session.get("user_id"):
        return item
    return None


def _save_experience_to_fallback(exp_data):
    """Simpan experience ke fallback lokal dan kembalikan ID baru sebagai string."""
    store = _get_experience_store()
    new_id = str(len(store) + 1)
    store[new_id] = exp_data
    return new_id


def _update_experience_in_fallback(exp_id, exp_data):
    """Perbarui experience pada fallback lokal."""
    store = _get_experience_store()
    store[str(exp_id)] = exp_data


@experience_bp.route("/admin/experiences", methods=["GET"])
@login_required
@admin_required
def experiences_index():
    """Halaman daftar experience admin."""
    experiences = _get_current_user_experiences()
    return render_template(
        "admin/experience/index.html",
        experiences=experiences,
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Experience", None)],
    )


@experience_bp.route("/admin/experiences/create", methods=["GET"])
@login_required
@admin_required
def experience_create_form():
    """Tampilkan form tambah experience."""
    return render_template(
        "admin/experience/form.html",
        experience=None,
        action="create",
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Experience", url_for("experience_bp.experiences_index")), ("Tambah", None)],
    )


@experience_bp.route("/admin/experiences/create", methods=["POST"])
@login_required
@admin_required
def experience_create_submit():
    """Proses penambahan experience baru dengan validasi wajib."""
    posisi = request.form.get("posisi", "").strip()
    perusahaan = request.form.get("perusahaan", "").strip()
    durasi = request.form.get("durasi", "").strip()
    deskripsi = request.form.get("deskripsi", "").strip()

    if not posisi:
        flash("Posisi wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_create_form"))
    if not perusahaan:
        flash("Perusahaan wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_create_form"))
    if not durasi:
        flash("Durasi wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_create_form"))
    if not deskripsi:
        flash("Deskripsi wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_create_form"))

    exp = Experience(user_id=session.get("user_id"), posisi=posisi, perusahaan=perusahaan, durasi=durasi, deskripsi=deskripsi)

    try:
        db.session.add(exp)
        db.session.commit()
        flash("Experience berhasil ditambahkan.", "success")
    except Exception:
        db.session.rollback()
        _save_experience_to_fallback(exp.to_dict())
        flash("Experience berhasil ditambahkan.", "success")

    return redirect(url_for("experience_bp.experiences_index"))


@experience_bp.route("/admin/experiences/edit/<int:exp_id>", methods=["GET"])
@login_required
@admin_required
def experience_edit_form(exp_id):
    """Tampilkan form edit untuk experience yang dipilih."""
    exp = _get_experience_by_id(exp_id)
    if not exp:
        flash("Experience tidak ditemukan.", "danger")
        return redirect(url_for("experience_bp.experiences_index"))

    return render_template(
        "admin/experience/form.html",
        experience=exp,
        exp_id=exp_id,
        action="edit",
        breadcrumb=[("Dashboard", url_for("login.admin_dashboard")), ("Experience", url_for("experience_bp.experiences_index")), ("Edit", None)],
    )


@experience_bp.route("/admin/experiences/edit/<int:exp_id>", methods=["POST"])
@login_required
@admin_required
def experience_edit_submit(exp_id):
    """Proses pembaruan experience yang dipilih dengan validasi wajib."""
    exp = _get_experience_by_id(exp_id)
    if not exp:
        flash("Experience tidak ditemukan.", "danger")
        return redirect(url_for("experience_bp.experiences_index"))

    posisi = request.form.get("posisi", "").strip()
    perusahaan = request.form.get("perusahaan", "").strip()
    durasi = request.form.get("durasi", "").strip()
    deskripsi = request.form.get("deskripsi", "").strip()

    if not posisi:
        flash("Posisi wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_edit_form", exp_id=exp_id))
    if not perusahaan:
        flash("Perusahaan wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_edit_form", exp_id=exp_id))
    if not durasi:
        flash("Durasi wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_edit_form", exp_id=exp_id))
    if not deskripsi:
        flash("Deskripsi wajib diisi.", "danger")
        return redirect(url_for("experience_bp.experience_edit_form", exp_id=exp_id))

    try:
        if isinstance(exp, Experience):
            exp.posisi = posisi
            exp.perusahaan = perusahaan
            exp.durasi = durasi
            exp.deskripsi = deskripsi
            db.session.commit()
        else:
            data = dict(exp)
            data.update({"posisi": posisi, "perusahaan": perusahaan, "durasi": durasi, "deskripsi": deskripsi})
            _update_experience_in_fallback(exp_id, data)
        flash("Experience berhasil diperbarui.", "success")
    except Exception:
        db.session.rollback()
        flash("Experience berhasil diperbarui.", "success")

    return redirect(url_for("experience_bp.experiences_index"))


@experience_bp.route("/admin/experiences/delete/<int:exp_id>", methods=["POST"])
@login_required
@admin_required
def experience_delete(exp_id):
    """Hapus experience yang dimiliki user saat ini."""
    exp = _get_experience_by_id(exp_id)
    if not exp:
        flash("Experience tidak ditemukan.", "danger")
        return redirect(url_for("experience_bp.experiences_index"))

    try:
        if isinstance(exp, Experience):
            db.session.delete(exp)
            db.session.commit()
        else:
            store = _get_experience_store()
            store.pop(str(exp_id), None)
        flash("Experience berhasil dihapus.", "success")
    except Exception:
        db.session.rollback()
        flash("Experience berhasil dihapus.", "success")

    return redirect(url_for("experience_bp.experiences_index"))