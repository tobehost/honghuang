# app/api/v1/user.py

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extentions.jwt import jwt_required, get_jwt_identity
from models import user
from app.extentions.db_postgres import db

user_bp = Blueprint('user', __name__, url_prefix='/api/v1/user')

def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'membership_level': user.membership_level,
        'created_at': user.created_at.isoformat()
    }

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户的资料"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': '用户未找到'}), 404
    return jsonify(serialize_user(user)), 200

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新当前用户的资料"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': '用户未找到'}), 404

    data = request.get_json()
    if data.get('username'):
        user.username = data['username']
    if data.get('membership_level'):
        user.membership_level = data['membership_level']

    db.session.commit()
    return jsonify({'message': '用户资料已更新'}), 200

@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户未找到'}), 404
    return jsonify(serialize_user(user)), 200


@user_bp.route('/user/register', methods=['GET'])
def register():
    """用户注册"""
    try:
        from werkzeug.security import generate_password_hash
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, membership_level)
            VALUES (%s, %s, %s)
        """, (username, password_hash, 'free'))
        
        conn.commit()
        logger.info(f"用户注册成功: {username}")
        return jsonify({'success': True, 'message': '注册成功'})
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': '注册失败'}), 500

@user_bp.route('/user/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        from werkzeug.security import check_password_hash
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user[2], password):
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        access_token = create_access_token(identity=user[0])
        logger.info(f"用户登录成功: {username}")
        
        return jsonify({
            'success': True,
            'token': access_token,
            'user': {
                'id': user[0],
                'username': user[1],
                'membership_level': user[3],
                'created_at': user[4].isoformat() if user[4] else None
            }
        })
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        return jsonify({'success': False, 'message': '登录失败'}), 500
    
@user_bp.route('/user/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        blacklist.add(jti)
        logger.info(f"用户已登出, jti: {jti}")
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        logger.error(f"用户登出失败: {str(e)}")
        return jsonify({'success': False, 'message': '登出失败'}), 500
    
@user_bp.route('/api/user/info', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取用户信息"""
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': user[0],
                'username': user[1],
                'membership_level': user[3],
                'created_at': user[4].isoformat() if user[4] else None
            }
        })
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取用户信息失败'}), 500
