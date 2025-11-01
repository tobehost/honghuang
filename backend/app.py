# primordial-culture-site-311714/backend/app.py
import os
import sys
import logging
from datetime import timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 设置全局异常捕获
def global_exception_handler(exctype, value, traceback):
    logging.critical("未捕获的全局异常", exc_info=(exctype, value, traceback))

sys.excepthook = global_exception_handler

# 严格按照如下方式配置静态资源
static_folder = '../frontend/public' if os.path.exists('../frontend/public') else '../frontend/dist'
app = Flask(__name__, static_folder=static_folder, static_url_path='/')

# Flask 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'primordial-culture-secret-key-2025')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-primordial-2025')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# CORS 配置
CORS(app, resources={r"/api/*": {"origins": "*"}})

# JWT 配置
jwt = JWTManager(app)

# 数据库连接配置（从环境变量获取）
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'app_dev_1'),
    'user': os.getenv('DB_USER', 'dev_374966547317260288'),
    'password': os.getenv('DB_PASSWORD', 'Vm0wFm8Qwly5'),
    'host': os.getenv('DB_HOST', '10.10.2.100'),
    'port': os.getenv('DB_PORT', '31853')
}

# 全局数据库连接对象
db_connection = None

def get_db_connection():
    """获取数据库连接"""
    global db_connection
    try:
        import psycopg2
        from psycopg2 import pool
        
        if db_connection is None or db_connection.closed:
            db_connection = psycopg2.connect(**DB_CONFIG)
            logger.info(f"成功连接到 PostgreSQL 数据库: {DB_CONFIG['dbname']}")
        
        return db_connection
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return None

def init_database():
    """初始化数据库表结构"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.warning("数据库连接失败，跳过初始化")
            return False
        
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                membership_level VARCHAR(20) DEFAULT 'free',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # 创建内容表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contents (
                id SERIAL PRIMARY KEY,
                type VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                price FLOAT DEFAULT 0.0,
                image_url VARCHAR(500),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # 创建订单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                content_id INTEGER NOT NULL REFERENCES contents(id),
                payment_status VARCHAR(20) DEFAULT 'pending',
                payment_time TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_type ON contents(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
        
        conn.commit()
        logger.info("数据库表结构初始化成功")
        
        # 检查是否需要插入示例数据
        cursor.execute("SELECT COUNT(*) FROM contents")
        content_count = cursor.fetchone()[0]
        
        if content_count == 0:
            logger.info("数据库为空，插入示例数据...")
            insert_sample_data(conn, cursor)
        
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False

def insert_sample_data(conn, cursor):
    """插入示例数据"""
    try:
        from werkzeug.security import generate_password_hash
        
        # 插入示例用户
        cursor.execute("""
            INSERT INTO users (username, password_hash, membership_level)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, ('admin', generate_password_hash('admin123'), 'vip'))
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, membership_level)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, ('test_user', generate_password_hash('test123'), 'free'))
        
        # 插入示例内容
        sample_contents = [
            ('novel', '洪荒纪元：开天辟地', '讲述盘古开天辟地的传说故事', 29.9, 
             'https://hpi-hub.tos-cn-beijing.volces.com/static/mobilewallpapers/cHJpdmF0ZS9sci91748499192317-7763YzJfMS5qcGc.jpg'),
            ('music', '洪荒之音：神话旋律', '古风音乐专辑，演绎洪荒时代的壮阔', 19.9,
             'https://hpi-hub.tos-cn-beijing.volces.com/static/batch_24/1757660354173-6723.jpg'),
            ('anime', '洪荒传说：神魔录', '动漫番剧，重现上古神魔之战', 39.9,
             'https://hpi-hub.tos-cn-beijing.volces.com/static/batch_20/1757610826493-2572.jpg'),
            ('wallpaper', '洪荒壁纸集：神韵典藏', '高清壁纸合集，展现洪荒美学', 9.9,
             'https://hpi-hub.tos-cn-beijing.volces.com/static/people/ai-generated-7957396_1280.png')
        ]
        
        for content in sample_contents:
            cursor.execute("""
                INSERT INTO contents (type, title, description, price, image_url)
                VALUES (%s, %s, %s, %s, %s)
            """, content)
        
        conn.commit()
        logger.info("示例数据插入成功")
    except Exception as e:
        logger.error(f"插入示例数据失败: {str(e)}")
        conn.rollback()

# 初始化数据库
try:
    init_database()
except Exception as e:
    logger.error(f"数据库初始化异常: {str(e)}")

# ==================== API 路由 ====================

@app.route('/api/content', methods=['GET'])
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

@app.route('/api/content/<int:content_id>', methods=['GET'])
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

@app.route('/api/user/register', methods=['POST'])
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

@app.route('/api/user/login', methods=['POST'])
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

@app.route('/api/user/info', methods=['GET'])
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

@app.route('/api/order', methods=['POST'])
@jwt_required()
def create_order():
    """创建订单"""
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        data = request.get_json()
        content_id = data.get('content_id')
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contents WHERE id = %s", (content_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': '内容不存在'}), 404
        
        cursor.execute("""
            INSERT INTO orders (user_id, content_id, payment_status)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (user_id, content_id, 'pending'))
        
        order_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"订单创建成功: 用户{user_id} 购买内容{content_id}")
        return jsonify({
            'success': True,
            'data': {'id': order_id},
            'message': '订单创建成功'
        })
    except Exception as e:
        logger.error(f"订单创建失败: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': '订单创建失败'}), 500

@app.route('/api/order/<int:order_id>/pay', methods=['POST'])
@jwt_required()
def pay_order(order_id):
    """支付订单"""
    try:
        from datetime import datetime
        
        user_id = get_jwt_identity()
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM orders 
            WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        
        order = cursor.fetchone()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        if order[4] == 'paid':
            return jsonify({'success': False, 'message': '订单已支付'}), 400
        
        cursor.execute("""
            UPDATE orders 
            SET payment_status = %s, payment_time = %s 
            WHERE id = %s
        """, ('paid', datetime.utcnow(), order_id))
        
        conn.commit()
        logger.info(f"订单支付成功: {order_id}")
        return jsonify({'success': True, 'message': '支付成功'})
    except Exception as e:
        logger.error(f"订单支付失败: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': '支付失败'}), 500

@app.route('/api/order', methods=['GET'])
@jwt_required()
def get_orders():
    """获取订单列表"""
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, c.title, c.price, c.type
            FROM orders o
            JOIN contents c ON o.content_id = c.id
            WHERE o.user_id = %s
            ORDER BY o.payment_time DESC
        """, (user_id,))
        
        orders = cursor.fetchall()
        order_list = []
        for order in orders:
            order_list.append({
                'id': order[0],
                'user_id': order[1],
                'content_id': order[2],
                'payment_status': order[3],
                'payment_time': order[4].isoformat() if order[4] else None,
                'content': {
                    'title': order[5],
                    'price': order[6],
                    'type': order[7]
                }
            })
        
        return jsonify({
            'success': True,
            'data': order_list,
            'total': len(order_list)
        })
    except Exception as e:
        logger.error(f"获取订单列表失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取订单列表失败'}), 500

# ==================== 静态文件路由 ====================

@app.route('/')
@app.route('/<path:path>')
def serve_static(path="index.html"):
    """提供静态文件服务"""
    try:
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return app.send_static_file('index.html')
    except Exception as e:
        logger.error(f"静态文件服务失败: {str(e)}")
        return jsonify({'success': False, 'message': '页面加载失败'}), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"正在启动 Flask 应用，端口: {port}")
    logger.info(f"静态文件目录: {app.static_folder}")
    logger.info(f"数据库配置: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    app.run(host='0.0.0.0', port=port, debug=True)