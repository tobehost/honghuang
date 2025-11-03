# app/app.py
import os
import sys
import logging
from datetime import timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from app.extentions.jwt import jwt

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
static_folder = '../app/static' if os.path.exists('../app/static') else '../app/static'
app = Flask(__name__, static_folder=static_folder, static_url_path='/')

# Flask 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'primordial-culture-secret-key-2025')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-primordial-2025')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# CORS 配置
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 注册蓝图
from app.api.v1.user import user_bp
from app.api.v1.content import content_bp
from app.api.v1.order import order_bp
app.register_blueprint(user_bp)
app.register_blueprint(content_bp)
app.register_blueprint(order_bp)


# ==================== 启动应用 ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"正在启动 Flask 应用，端口: {port}")
    logger.info(f"静态文件目录: {app.static_folder}")
    logger.info(f"数据库配置: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    app.run(host='0.0.0.0', port=port, debug=True)