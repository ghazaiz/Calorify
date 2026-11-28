from flask import Flask, jsonify, redirect, url_for
from flask_login import current_user
from sqlalchemy import event, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.extensions import db, login_manager
from app.core.config import Config
from app.core.http import wants_json

from app.authentication.routes import auth_bp
from app.profile.routes import profile_bp
from app.meals.routes import meals_bp
from app.nutrition.routes import nutrition_bp
from app.reports.routes import reports_bp

from app.profile.models import User, Profile
from app.meals.models import Meal
from app.version import APP_VERSION, RELEASE_NAME


@login_manager.unauthorized_handler
def login_required_response():
    if wants_json():
        return jsonify({"message": "Log in to continue"}), 401
    return redirect(url_for("authentication.login"))


@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def initialize_database():
    db.create_all()
    with db.engine.begin() as connection:
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        columns = {column["name"] for column in inspect(connection).get_columns(Profile.__tablename__)}
        if "weekly_loss" not in columns:
            connection.execute(text("ALTER TABLE profiles ADD COLUMN weekly_loss FLOAT"))
        # Targets are determined by the profile inputs and now calculated on read.
        for column in ("daily_calorie_target", "protein_target", "carbohydrates_target", "fats_target"):
            if column in columns:
                connection.exec_driver_sql(f"ALTER TABLE profiles DROP COLUMN {column}")
    for index in Meal.__table__.indexes:
        index.create(bind=db.engine, checkfirst=True)


def _enable_sqlite_foreign_keys(connection, _record):
    connection.execute("PRAGMA foreign_keys = ON")


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)
    Config.configure_production(app.config)

    db.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            event.listen(db.engine, "connect", _enable_sqlite_foreign_keys)

    login_manager.init_app(app)

    # Register all module blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(reports_bp)

    @app.cli.command("init-db")
    def init_db():
        """Create tables that are missing from the configured database."""
        initialize_database()

    @app.cli.command("app-version")
    def app_version():
        """Print the Calorify application version."""
        print(app.config["APP_VERSION"])

    @app.context_processor
    def inject_profile():
        if current_user.is_authenticated:
            return {
                "user_profile": Profile.query.filter_by(
                    user_id=current_user.user_id
                ).first(),
                "app_version": APP_VERSION,
                "release_name": RELEASE_NAME
            }
        return {
            "user_profile": None,
            "app_version": APP_VERSION,
            "release_name": RELEASE_NAME
        }

    @app.route("/", methods=["GET"])
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("reports.dashboard"))

        return redirect(url_for("authentication.login"))

    @app.get("/healthz")
    def health():
        try:
            for model in (User, Profile, Meal):
                db.session.execute(select(model).limit(0))
        except SQLAlchemyError:
            app.logger.exception("Database readiness check failed")
            return jsonify(status="unavailable"), 503
        return jsonify(status="ok", version=APP_VERSION)

    return app
