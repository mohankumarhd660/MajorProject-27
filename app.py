import os

from dotenv import load_dotenv
from flask import Flask

from utils.security import configure_security
from utils.db import init_db
from utils.login import init_login
from routes.auth import auth_bp
from routes.student import student_bp
from routes.teacher import teacher_bp
from routes.api import api_bp
from services.dataset_loader import load_dataset_into_db
from faiss_engine.indexer import build_or_load_index
from services.firebase_service import init_firebase


def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    configure_security(app)
    init_login(app)
    init_db(app)
    
    # Initialize Firebase (optional - app works without it)
    init_firebase()

    # load_dataset_into_db()
    # build_or_load_index(force_rebuild=False)

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
