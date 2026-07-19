from flask import Blueprint, request, jsonify
from model import Database
from Backend.admin.login import token_required

skills_bp = Blueprint('skills', __name__)

# ✅ PERBAIKAN: Hapus '/api' di depan route
@skills_bp.route('/skills', methods=['GET'])
def get_skills():
    """Mengambil semua skills (publik)"""
    try:
        db = Database()
        
        query = """
            SELECT s.*, u.username 
            FROM skills s 
            JOIN users u ON s.user_id = u.id 
            WHERE u.role = 'admin'
            ORDER BY s.id DESC
        """
        result = db.execute_query(query, fetch=True)
        
        return jsonify({
            'success': True,
            'data': result if result else []
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/skills/<int:id>', methods=['GET'])
def get_skill_by_id(id):
    """Mengambil satu skill berdasarkan ID"""
    try:
        db = Database()
        
        query = "SELECT * FROM skills WHERE id = %s"
        result = db.execute_query(query, (id,), fetch=True)
        
        if not result:
            return jsonify({'error': 'Skill tidak ditemukan'}), 404
        
        return jsonify({
            'success': True,
            'data': result[0]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/skills', methods=['POST'])
@token_required
def create_skill(current_user):
    """Create skill baru"""
    try:
        data = request.get_json()
        
        required_fields = ['nama_skill']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} wajib diisi'}), 400
        
        db = Database()
        
        query = """
            INSERT INTO skills (user_id, nama_skill, icon_class)
            VALUES (%s, %s, %s)
        """
        values = (
            current_user,
            data.get('nama_skill'),
            data.get('icon_class')
        )
        
        new_id = db.execute_query(query, values)
        
        return jsonify({
            'success': True,
            'message': 'Skill berhasil dibuat',
            'id': new_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/skills/<int:id>', methods=['PUT'])
@token_required
def update_skill(current_user, id):
    """Update skill"""
    try:
        data = request.get_json()
        
        db = Database()
        
        # Cek apakah skill milik user ini
        check_query = "SELECT id FROM skills WHERE id = %s AND user_id = %s"
        existing = db.execute_query(check_query, (id, current_user), fetch=True)
        
        if not existing:
            return jsonify({'error': 'Skill tidak ditemukan atau bukan milik Anda'}), 404
        
        allowed_fields = ['nama_skill', 'icon_class']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        
        if not updates:
            return jsonify({'error': 'Tidak ada data yang diupdate'}), 400
        
        values.append(id)
        query = f"UPDATE skills SET {', '.join(updates)} WHERE id = %s"
        db.execute_query(query, tuple(values))
        
        return jsonify({
            'success': True,
            'message': 'Skill berhasil diupdate'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/skills/<int:id>', methods=['DELETE'])
@token_required
def delete_skill(current_user, id):
    """Delete skill"""
    try:
        db = Database()
        
        # Cek apakah skill milik user ini
        check_query = "SELECT id FROM skills WHERE id = %s AND user_id = %s"
        existing = db.execute_query(check_query, (id, current_user), fetch=True)
        
        if not existing:
            return jsonify({'error': 'Skill tidak ditemukan atau bukan milik Anda'}), 404
        
        query = "DELETE FROM skills WHERE id = %s"
        db.execute_query(query, (id,))
        
        return jsonify({
            'success': True,
            'message': 'Skill berhasil dihapus'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500