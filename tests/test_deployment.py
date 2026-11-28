from sqlalchemy import text

from app import create_app
from app.core.extensions import db
from app.version import APP_VERSION


def test_readiness_reports_the_version_with_initialized_schema():
    response = create_app().test_client().get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": APP_VERSION}


def test_readiness_fails_when_the_schema_is_missing():
    app = create_app()
    with app.app_context():
        db.session.execute(text("DROP TABLE meals"))
        db.session.commit()

    response = app.test_client().get("/healthz")
    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
