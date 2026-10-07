import pytest

from app import create_app
from app.core.extensions import db


@pytest.fixture(autouse=True)
def reset_database():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield