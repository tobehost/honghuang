# primordial-culture-site-311714/backend/admin.py
import os
import csv
import io
from datetime import datetime
from flask import Flask, redirect, url_for, request, make_response, flash
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()

class SecureModelView(ModelView):
    """安全的模型视图基类，添加权限验证"""
    def is_accessible(self):
        return request.cookies.get('admin_logged_in') == 'true'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))

class UserModelView(SecureModelView):
    """用户管理视图"""
    column_list = ['id', 'username', 'membership_level', 'created_at']
    column_labels = {
        'id': '用户ID',
        'username': '用户名',
        'membership_level': '会员等级',
        'created_at': '注册时间'
    }
    column_searchable_list = ['username']
    column_filters = ['membership_level', 'created_at']
    column_default_sort = ('created_at', True)
    can_create = False
    can_edit = True
    can_delete = False
    form_excluded_columns = ['password_hash', 'orders']
    
    column_formatters = {
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else '-'
    }

class ContentModelView(SecureModelView):
    """内容管理视图"""
    column_list = ['id', 'type', 'title', 'price', 'created_at']
    column_labels = {
        'id': '内容ID',
        'type': '类型',
        'title': '标题',
        'description': '描述',
        'price': '价格',
        'image_url': '图片地址',
        'created_at': '发布时间'
    }
    column_searchable_list = ['title', 'description']
    column_filters = ['type', 'price', 'created_at']
    column_default_sort = ('created_at', True)
    form_choices = {
        'type': [
            ('novel', '小说'),
            ('music', '音乐'),
            ('anime', '动漫'),
            ('wallpaper', '壁纸')
        ]
    }
    
    column_formatters = {
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else '-',
        'price': lambda v, c, m, p: f'¥{m.price:.2f}'
    }

class OrderModelView(SecureModelView):
    """订单管理视图"""
    column_list = ['id', 'user_id', 'content_id', 'payment_status', 'payment_time']
    column_labels = {
        'id': '订单ID',
        'user_id': '用户ID',
        'content_id': '内容ID',
        'payment_status': '支付状态',
        'payment_time': '支付时间'
    }
    column_filters = ['payment_status', 'payment_time']
    column_default_sort = ('payment_time', True)
    can_create = False
    can_edit = True
    can_delete = False
    form_choices = {
        'payment_status': [
            ('pending', '待支付'),
            ('paid', '已支付'),
            ('cancelled', '已取消'),
            ('refunded', '已退款')
        ]
    }
    
    column_formatters = {
        'payment_time': lambda v, c, m, p: m.payment_time.strftime('%Y-%m-%d %H:%M:%S') if m.payment_time else '-'
    }

class DataStatisticsView(BaseView):
    """数据统计视图"""
    def is_accessible(self):
        return request.cookies.get('admin_logged_in') == 'true'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))
    
    @expose('/')
    def index(self):
        try:
            from models import User, Content, Order
            
            total_users = User.query.count()
            vip_users = User.query.filter_by(membership_level='vip').count()
            total_contents = Content.query.count()
            total_orders = Order.query.count()
            paid_orders = Order.query.filter_by(payment_status='paid').count()
            
            content_stats = db.session.query(
                Content.type,
                db.func.count(Content.id)
            ).group_by(Content.type).all()
            
            order_stats = db.session.query(
                Order.payment_status,
                db.func.count(Order.id)
            ).group_by(Order.payment_status).all()
            
            revenue = db.session.query(
                db.func.sum(Content.price)
            ).join(Order, Order.content_id == Content.id).filter(
                Order.payment_status == 'paid'
            ).scalar() or 0
            
            stats = {
                'total_users': total_users,
                'vip_users': vip_users,
                'total_contents': total_contents,
                'total_orders': total_orders,
                'paid_orders': paid_orders,
                'revenue': float(revenue),
                'content_stats': dict(content_stats),
                'order_stats': dict(order_stats)
            }
            
            return self.render('admin/statistics.html', stats=stats)
        
        except Exception as e:
            logger.error(f"数据统计失败: {str(e)}")
            return self.render('admin/statistics.html', stats={}, error=str(e))

class DataExportView(BaseView):
    """数据导出视图"""
    def is_accessible(self):
        return request.cookies.get('admin_logged_in') == 'true'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))
    
    @expose('/export-users/')
    def export_users(self):
        try:
            from models import User
            
            users = User.query.all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['用户ID', '用户名', '会员等级', '注册时间'])
            
            for user in users:
                writer.writerow([
                    user.id,
                    user.username,
                    user.membership_level,
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '-'
                ])
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename=users_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
            
            logger.info("用户数据导出成功")
            return response
        
        except Exception as e:
            logger.error(f"用户数据导出失败: {str(e)}")
            return f"导出失败: {str(e)}", 500
    
    @expose('/export-orders/')
    def export_orders(self):
        try:
            from models import Order, User, Content
            
            orders = db.session.query(Order, User, Content).join(
                User, Order.user_id == User.id
            ).join(
                Content, Order.content_id == Content.id
            ).all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['订单ID', '用户名', '内容标题', '内容类型', '价格', '支付状态', '支付时间'])
            
            for order, user, content in orders:
                writer.writerow([
                    order.id,
                    user.username,
                    content.title,
                    content.type,
                    f'{content.price:.2f}',
                    order.payment_status,
                    order.payment_time.strftime('%Y-%m-%d %H:%M:%S') if order.payment_time else '-'
                ])
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename=orders_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
            
            logger.info("订单数据导出成功")
            return response
        
        except Exception as e:
            logger.error(f"订单数据导出失败: {str(e)}")
            return f"导出失败: {str(e)}", 500
    
    @expose('/export-contents/')
    def export_contents(self):
        try:
            from models import Content
            
            contents = Content.query.all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['内容ID', '类型', '标题', '描述', '价格', '发布时间'])
            
            for content in contents:
                writer.writerow([
                    content.id,
                    content.type,
                    content.title,
                    content.description or '-',
                    f'{content.price:.2f}',
                    content.created_at.strftime('%Y-%m-%d %H:%M:%S') if content.created_at else '-'
                ])
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename=contents_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
            
            logger.info("内容数据导出成功")
            return response
        
        except Exception as e:
            logger.error(f"内容数据导出失败: {str(e)}")
            return f"导出失败: {str(e)}", 500

class SecureAdminIndexView(AdminIndexView):
    """自定义管理后台首页，添加登录功能"""
    @expose('/')
    def index(self):
        if request.cookies.get('admin_logged_in') != 'true':
            return redirect(url_for('.login_view'))
        
        try:
            from models import User, Content, Order
            
            total_users = User.query.count()
            total_contents = Content.query.count()
            total_orders = Order.query.count()
            paid_orders = Order.query.filter_by(payment_status='paid').count()
            
            revenue = db.session.query(
                db.func.sum(Content.price)
            ).join(Order, Order.content_id == Content.id).filter(
                Order.payment_status == 'paid'
            ).scalar() or 0
            
            stats = {
                'total_users': total_users,
                'total_contents': total_contents,
                'total_orders': total_orders,
                'paid_orders': paid_orders,
                'revenue': float(revenue)
            }
            
            return self.render('admin/index.html', stats=stats)
        
        except Exception as e:
            logger.error(f"加载首页数据失败: {str(e)}")
            return self.render('admin/index.html', stats={})
    
    @expose('/login', methods=['GET', 'POST'])
    def login_view(self):
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            
            if username == 'admin' and password == 'admin123':
                response = redirect(url_for('admin.index'))
                response.set_cookie('admin_logged_in', 'true', max_age=3600*24)
                logger.info(f"管理员 {username} 登录成功")
                return response
            else:
                logger.warning(f"管理员登录失败: {username}")
                return self.render('admin/login.html', error='用户名或密码错误')
        
        return self.render('admin/login.html')
    
    @expose('/logout')
    def logout_view(self):
        response = redirect(url_for('.login_view'))
        response.set_cookie('admin_logged_in', '', expires=0)
        logger.info("管理员已退出")
        return response

def init_admin(app, db_instance):
    """初始化Flask-Admin"""
    try:
        from models import User, Content, Order
        
        admin = Admin(
            app,
            name='洪荒文化IP数据中台',
            template_mode='bootstrap4',
            index_view=SecureAdminIndexView(name='数据概览', url='/admin')
        )
        
        admin.add_view(UserModelView(User, db_instance.session, name='用户管理', endpoint='user'))
        admin.add_view(ContentModelView(Content, db_instance.session, name='内容管理', endpoint='content'))
        admin.add_view(OrderModelView(Order, db_instance.session, name='订单管理', endpoint='order'))
        admin.add_view(DataStatisticsView(name='数据统计', endpoint='statistics'))
        admin.add_view(DataExportView(name='数据导出', endpoint='export'))
        
        logger.info("Flask-Admin初始化成功")
        return admin
    
    except Exception as e:
        logger.error(f"Flask-Admin初始化失败: {str(e)}")
        return None