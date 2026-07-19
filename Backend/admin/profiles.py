from flask import Blueprint, request, jsonify
from model import Database
from Backend.admin.login import token_required

profiles_bp = Blueprint('profiles', __name__)

@profiles_bp.route('/profiles', methods=['GET'])
@token_required
def get_profil(current_user):
    try:
        db = Database()
        query = "SELECT * FROM profiles WHERE user_id = %s"
        result = db.execute_query(query, (current_user,), fetch=True)
        
        if result:
            return jsonify({'success': True, 'data': result[0]}), 200
        else:
            return jsonify({'success': True, 'data': {}}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profiles_bp.route('/profiles', methods=['POST', 'PUT'])
@token_required
def update_profil(current_user):
    try:
        data = request.get_json()
        db = Database()

        # Cek apakah profiles sudah ada
        check_query = "SELECT id FROM profiles WHERE user_id = %s"
        existing = db.execute_query(check_query, (current_user,), fetch=True)

        # Field yang diizinkan (SESUAIKAN DENGAN KOLOM DI DATABASE KAMU)
        allowed_fields = [
            'nama_lengkap', 'nama_panggilan', 'tempat_lahir', 'tanggal_lahir',
            'email', 'telepon', 'universitas', 'fakultas', 'prodi', 
            'semester', 'alamat', 'foto_url'
        ]

        updates = []
        values = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])

        if not updates:
            return jsonify({'error': 'Tidak ada data valid untuk diupdate'}), 400

        if existing:
            # UPDATE
            values.append(current_user)
            query = f"UPDATE profiles SET {', '.join(updates)} WHERE user_id = %s"
        else:
            fields_str = ', '.join([f.split(' = ')[0] for f in updates])
            placeholders = ', '.join(['%s'] * len(updates))
            values.insert(0, current_user) 
            query = f"INSERT INTO profiles (user_id, {fields_str}) VALUES (%s, {placeholders})"

        db.execute_query(query, tuple(values))
        
        return jsonify({'success': True, 'message': 'Profil berhasil disimpan'}), 200

    except Exception as e:
        print(f"DEBUG ERROR PROFIL: {str(e)}") # Cek terminal untuk error detail
        return jsonify({'error': str(e)}), 500