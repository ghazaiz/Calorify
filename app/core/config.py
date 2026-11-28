
import os
from secrets import token_hex

from dotenv import load_dotenv

from app.version import APP_VERSION

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    APP_VERSION = APP_VERSION
    SECRET_KEY = os.getenv("SECRET_KEY") or token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "calorify.db")
    )

    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def configure_production(cls, config):
        if os.getenv("APP_ENV") != "production":
            return
        if not os.getenv("SECRET_KEY") or not os.getenv("DATABASE_URL"):
            raise RuntimeError("Production requires SECRET_KEY and DATABASE_URL.")
        config.update(
            SECRET_KEY=os.environ["SECRET_KEY"],
            SQLALCHEMY_DATABASE_URI=os.environ["DATABASE_URL"],
            DEBUG=False,
            SESSION_COOKIE_SECURE=True,
        )
