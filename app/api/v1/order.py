# api/v1/order.py
from flask import Blueprint, request, jsonify
from app.extentions.jwt import jwt_required, get_jwt_identity
from app.extentions.db_postgres import db
import logging

logger = logging.getLogger(__name__)

order_bp = Blueprint('order', __name__, url_prefix='/api/v1/order')

@order_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    """创建订单"""
    try:
        user_id = get_jwt_identity()
        conn = db.connect()
        
        data = request.get_json()
        content_id = data.get('content_id')
        
        cursor = conn.execute("SELECT * FROM contents WHERE id = %s", (content_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': '内容不存在'}), 404
        
        cursor = conn.execute("""
            INSERT INTO orders (user_id, content_id, status, created_at)
            VALUES (%s, %s, %s, NOW()) RETURNING id
        """, (user_id, content_id, 'pending'))
        
        order_id = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({'success': True, 'order_id': order_id}), 201
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        return jsonify({'success': False, 'message': '创建订单失败'}), 500
    

@order_bp.route('/<int:order_id>/pay', methods=['POST'])
@jwt_required()
def pay_order(order_id):
    """支付订单"""
    try:
        from datetime import datetime
        
        user_id = get_jwt_identity()
        conn = db.connect()
        
        cursor = conn.execute("""
            SELECT * FROM orders WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        order = cursor.fetchone()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        conn.execute("""
            UPDATE orders SET status = %s, payment_time = %s WHERE id = %s
        """, ('paid', datetime.utcnow(), order_id))
        
        conn.close()
        
        return jsonify({'success': True, 'message': '订单支付成功'}), 200
    except Exception as e:
        logger.error(f"支付订单失败: {str(e)}")
        return jsonify({'success': False, 'message': '支付订单失败'}), 500
    

@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """获取订单详情"""
    try:
        user_id = get_jwt_identity()
        conn = db.connect()
        
        cursor = conn.execute("""
            SELECT * FROM orders WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        order = cursor.fetchone()
        conn.close()
        
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        order_data = {
            'id': order[0],
            'user_id': order[1],
            'content_id': order[2],
            'status': order[3],
            'payment_time': order[4].isoformat() if order[4] else None
        }
        
        return jsonify({'success': True, 'data': order_data}), 200
    except Exception as e:
        logger.error(f"获取订单详情失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取订单详情失败'}), 500
    

@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    """获取订单列表"""
    try:
        user_id = get_jwt_identity()
        conn = db.connect()
        
        cursor = conn.execute("""
            SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC
        """, (user_id,))
        orders = cursor.fetchall()
        conn.close()
        
        orders_list = []
        for order in orders:
            orders_list.append({
                'id': order[0],
                'user_id': order[1],
                'content_id': order[2],
                'status': order[3],
                'payment_time': order[4].isoformat() if order[4] else None
            })
        
        return jsonify({'success': True, 'data': orders_list}), 200
    except Exception as e:
        logger.error(f"获取订单列表失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取订单列表失败'}), 500
    

@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """取消订单"""
    try:
        user_id = get_jwt_identity()
        conn = db.connect()
        
        cursor = conn.execute("""
            SELECT * FROM orders WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        order = cursor.fetchone()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        if order[3] == 'paid':
            return jsonify({'success': False, 'message': '已支付订单无法取消'}), 400
        
        conn.execute("""
            UPDATE orders SET status = %s WHERE id = %s
        """, ('canceled', order_id))
        
        conn.close()
        
        return jsonify({'success': True, 'message': '订单取消成功'}), 200
    except Exception as e:
        logger.error(f"取消订单失败: {str(e)}")
        return jsonify({'success': False, 'message': '取消订单失败'}), 500
    

@order_bp.route('/stats', methods=['GET'])
@jwt_required()
def order_stats():
    """获取订单统计数据"""
    try:
        user_id = get_jwt_identity()
        conn = db.connect()
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM orders WHERE user_id = %s
        """, (user_id,))
        total_orders = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM orders WHERE user_id = %s AND status = %s
        """, (user_id, 'paid'))
        paid_orders = cursor.fetchone()[0]
        
        conn.close()
        
        stats = {
            'total_orders': total_orders,
            'paid_orders': paid_orders
        }
        
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        logger.error(f"获取订单统计数据失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取订单统计数据失败'}), 500
    
