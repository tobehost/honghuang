# app/api/v1/auth.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')