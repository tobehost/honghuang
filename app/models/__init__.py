# primordial-culture-site-311714/backend/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()


def init_database(app):
    """初始化数据库"""
    try:
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            
            if User.query.count() == 0:
                admin_user = User(username='admin', membership_level='vip')
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                
                test_user = User(username='test_user', membership_level='free')
                test_user.set_password('test123')
                db.session.add(test_user)
                
                sample_contents = [
                    Content(
                        type='novel',
                        title='洪荒纪元：开天辟地',
                        description='讲述盘古开天辟地的传说故事',
                        price=29.9,
                        image_url='https://hpi-hub.tos-cn-beijing.volces.com/static/mobilewallpapers/cHJpdmF0ZS9sci91748499192317-7763YzJfMS5qcGc.jpg'
                    ),
                    Content(
                        type='music',
                        title='洪荒之音：神话旋律',
                        description='古风音乐专辑，演绎洪荒时代的壮阔',
                        price=19.9,
                        image_url='https://hpi-hub.tos-cn-beijing.volces.com/static/batch_24/1757660354173-6723.jpg'
                    ),
                    Content(
                        type='anime',
                        title='洪荒传说：神魔录',
                        description='动漫番剧，重现上古神魔之战',
                        price=39.9,
                        image_url='https://hpi-hub.tos-cn-beijing.volces.com/static/batch_20/1757610826493-2572.jpg'
                    ),
                    Content(
                        type='wallpaper',
                        title='洪荒壁纸集：神韵典藏',
                        description='高清壁纸合集，展现洪荒美学',
                        price=9.9,
                        image_url='https://hpi-hub.tos-cn-beijing.volces.com/static/people/ai-generated-7957396_1280.png'
                    )
                ]
                
                for content in sample_contents:
                    db.session.add(content)
                
                db.session.commit()
                logger.info("数据库初始化成功，已添加示例数据")
            else:
                logger.info("数据库已存在，跳过初始化")
                
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")