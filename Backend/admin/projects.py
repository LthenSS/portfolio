from flask import Blueprint, request, jsonify
from model import Database
from Backend.admin.login import token_required

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects', methods=['GET'])
def get_projects():
    """Mengambil semua projects (publik)"""
    try:
        db = Database()
        
        # Sesuai DB: Ambil judul, deskripsi, gambar_url, link_project
        query = """
            SELECT p.*, u.username 
            FROM projects p 
            JOIN users u ON p.user_id = u.id 
            WHERE u.role = 'admin'
            ORDER BY p.created_at DESC
        """
        result = db.execute_query(query, fetch=True)
        
        return jsonify({
            'success': True,
            'data': result if result else []
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<int:id>', methods=['GET'])
def get_project_by_id(id):
    """Mengambil satu project berdasarkan ID"""
    try:
        db = Database()
        query = "SELECT * FROM projects WHERE id = %s"
        result = db.execute_query(query, (id,), fetch=True)
        
        if not result:
            return jsonify({'error': 'Project tidak ditemukan'}), 404
        
        return jsonify({
            'success': True,
            'data': result[0]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects', methods=['POST'])
@token_required
def create_project(current_user):
    """Create project baru"""
    try:
        data = request.get_json()
        
        required_fields = ['judul', 'deskripsi']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} wajib diisi'}), 400
        
        db = Database()
        
        # Sesuai DB: user_id, judul, deskripsi, gambar_url, link_project
        query = """
            INSERT INTO projects (user_id, judul, deskripsi, gambar_url, link_project)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            current_user,
            data.get('judul'),
            data.get('deskripsi'),
            data.get('gambar_url'), # Bisa kosong/null
            data.get('link_project') # Bisa kosong/null
        )
        
        new_id = db.execute_query(query, values)
        
        return jsonify({
            'success': True,
            'message': 'Project berhasil dibuat',
            'id': new_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<int:id>', methods=['PUT'])
@token_required
def update_project(current_user, id):
    """Update project"""
    try:
        data = request.get_json()
        db = Database()
        
        check_query = "SELECT id FROM projects WHERE id = %s AND user_id = %s"
        existing = db.execute_query(check_query, (id, current_user), fetch=True)
        
        if not existing:
            return jsonify({'error': 'Project tidak ditemukan atau bukan milik Anda'}), 404
        
        # Allowed fields sesuai kolom DB
        allowed_fields = ['judul', 'deskripsi', 'gambar_url', 'link_project']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        
        if not updates:
            return jsonify({'error': 'Tidak ada data yang diupdate'}), 400
        
        values.append(id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = %s"
        db.execute_query(query, tuple(values))
        
        return jsonify({
            'success': True,
            'message': 'Project berhasil diupdate'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<int:id>', methods=['DELETE'])
@token_required
def delete_project(current_user, id):
    """Delete project"""
    try:
        db = Database()
        check_query = "SELECT id FROM projects WHERE id = %s AND user_id = %s"
        existing = db.execute_query(check_query, (id, current_user), fetch=True)
        
        if not existing:
            return jsonify({'error': 'Project tidak ditemukan atau bukan milik Anda'}), 404
        
        query = "DELETE FROM projects WHERE id = %s"
        db.execute_query(query, (id,))
        
        return jsonify({
            'success': True,
            'message': 'Project berhasil dihapus'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500