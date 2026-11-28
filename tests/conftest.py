import pytest

from app import create_app
from app.core.config import Config
from app.core.extensions import db


@pytest.fixture(autouse=True)
def reset_database(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{tmp_path / 'calorify-test.db'}")
    app = create_app()
    with app.app_context():
        db.create_all()
        db.engine.dispose()
