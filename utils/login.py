from flask import jsonify, request
from flask_login import LoginManager

from models.user import User
from utils.db import get_db_session

login_manager = LoginManager()
login_manager.login_view = "auth.login"


def init_login(app):
    login_manager.init_app(app)


@login_manager.unauthorized_handler
def _unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"error": "Unauthorized"}), 401
    return login_manager.unauthorized()


@login_manager.user_loader
def load_user(user_id: str):
    db = get_db_session()
    return db.query(User).filter(User.id == int(user_id)).first()
