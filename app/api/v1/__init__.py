# app/api/v1/__init__.py

from flask import Blueprint

api = Blueprint('api', __name__)

from .user import users_bp
from .auth import auth_bp
from .content import content_bp
from .order import order_bp
from .static import static_bp

__all__ = ['users', 'auth', 'content', 'order', 'static']