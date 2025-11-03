# app.extentions.jwt.py

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

jwt = JWTManager()

# 配置 JWT 回调函数（如有需要）
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.identity

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from models import User
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

# 你可以根据需要添加更多的 JWT 配置和回调函数