import os
import tempfile

import pytest

from app import create_app
from app.core.config import Config
from app.core.extensions import db


# Point every app the tests create at a throwaway database file so the
# test suite can never touch the real calorify.db. This runs before the
# test modules are imported, so each create_app() call picks it up.
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "calorify_test.db")
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///" + TEST_DB_PATH


@pytest.fixture(autouse=True)
def reset_database():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield
