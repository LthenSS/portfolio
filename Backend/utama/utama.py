from flask import Blueprint, jsonify

# Blueprint dasar untuk endpoint halaman utama.
utama_bp = Blueprint("utama_bp", __name__)


@utama_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200
