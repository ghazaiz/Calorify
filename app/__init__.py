from flask import Flask
from dotenv import load_dotenv
from app.core.extensions import db, login_manager

from app.core.config import Config
from app.reports.routes import reports_bp
from app.authentication.routes import auth_bp
from app.profile.routes import profile_bp
from app.nutrition.routes import nutrition_bp
from app.meals.routes import meals_bp

from app.profile.models import User, Profile
from app.meals.models import Meal




load_dotenv()

@login_manager.user_loader
def load_user(user_id):
    from app.profile.models import User
    return db.session.get(User, int(user_id))

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    login_manager.init_app(app)

    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(meals_bp)

    return app