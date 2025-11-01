# primordial-culture-site-311714/backend/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()

class User(db.Model):
    """用户表模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    membership_level = db.Column(db.String(20), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'membership_level': self.membership_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Content(db.Model):
    """内容表模型"""
    __tablename__ = 'contents'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='content', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Content {self.title}>'

class Order(db.Model):
    """订单表模型"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    payment_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_id': self.content_id,
            'payment_status': self.payment_status,
            'payment_time': self.payment_time.isoformat() if self.payment_time else None
        }
    
    def __repr__(self):
        return f'<Order {self.id}>'

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