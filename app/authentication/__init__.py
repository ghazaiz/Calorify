
from flask import Flask

from app.core.config import Config
from app.core.extensions import db, login_manager


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.authentication.routes import auth_bp

    app.register_blueprint(auth_bp)

    return app
