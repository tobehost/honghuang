# app/api/v1/static.py
from flask import Blueprint, send_from_directory, current_app
import os

static_bp = Blueprint('static', __name__, url_prefix='/static')

@static_bp.route('/<path:filename>', methods=['GET'])
def serve_static_file(filename):
    """提供静态文件"""
    try:
        return send_from_directory(current_app.static_folder, filename)
    except Exception as e:
        logger.error(f"提供静态文件失败: {str(e)}")
        return jsonify({'success': False, 'message': '提供静态文件失败'}), 500