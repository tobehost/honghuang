# app.extentions.db_postgres.py
import os
import logging
logger = logging.getLogger(__name__)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

db = create_engine(
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

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

