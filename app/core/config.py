import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "calorify.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False