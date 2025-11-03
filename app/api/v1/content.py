# app/api/v1/content.py
from flask import Blueprint, request, jsonify
from app.extensions.db_postgres import get_db_connection
import logging

logger = logging.getLogger(__name__)
content_bp = Blueprint('content', __name__, url_prefix='/api/v1/content')


@content_bp.route('/api/content', methods=['GET'])
def get_content():
    """获取内容列表"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        content_type = request.args.get('type', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        offset = (page - 1) * limit
        
        if content_type:
            cursor.execute("""
                SELECT * FROM contents 
                WHERE type = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (content_type, limit, offset))
            
            cursor.execute("SELECT COUNT(*) FROM contents WHERE type = %s", (content_type,))
        else:
            cursor.execute("""
                SELECT * FROM contents 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            cursor.execute("SELECT COUNT(*) FROM contents")
        
        contents = cursor.fetchall()
        total = cursor.fetchone()[0]
        
        content_list = []
        for content in contents:
            content_list.append({
                'id': content[0],
                'type': content[1],
                'title': content[2],
                'description': content[3],
                'price': content[4],
                'image_url': content[5],
                'created_at': content[6].isoformat() if content[6] else None
            })
        
        return jsonify({
            'success': True,
            'data': content_list,
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit
        })
    except Exception as e:
        logger.error(f"获取内容失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取内容失败'}), 500

@content_bp.route('/api/content/<int:content_id>', methods=['GET'])
def get_content_detail(content_id):
    """获取内容详情"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contents WHERE id = %s", (content_id,))
        content = cursor.fetchone()
        
        if not content:
            return jsonify({'success': False, 'message': '内容不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': content[0],
                'type': content[1],
                'title': content[2],
                'description': content[3],
                'price': content[4],
                'image_url': content[5],
                'created_at': content[6].isoformat() if content[6] else None
            }
        })
    except Exception as e:
        logger.error(f"获取内容详情失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取内容详情失败'}), 500

