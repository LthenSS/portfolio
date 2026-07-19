import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, jsonify
from config import Config
from Backend.admin.login import token_required # Opsional: hapus decorator ini jika ingin publik

upload_bp = Blueprint('upload', __name__)

# Inisialisasi konfigurasi Cloudinary dari Config
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

@upload_bp.route('/upload/image', methods=['POST'])
@token_required # Pastikan hanya admin yang bisa upload
def upload_image(current_user):
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file yang diterima'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nama file tidak boleh kosong'}), 400
        
    try:
        # Upload ke Cloudinary dengan folder spesifik agar rapi
        result = cloudinary.uploader.upload(
            file, 
            folder="portfolio/projects",
            resource_type="image"
        )
        
        return jsonify({
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Upload gagal: {str(e)}'}), 500