# app/__init__.py

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from app.extentions.db_postgres import db

from flask import Flask
app = Flask(__name__)

def create_app():
    db.init_database()
    from app.api.v1.order import order_bp
    app.register_blueprint(order_bp)
    from app.api.v1.user import user_bp
    app.register_blueprint(user_bp)
    from app.api.v1.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    return app