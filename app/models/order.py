

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
