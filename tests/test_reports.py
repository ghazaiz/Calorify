from datetime import date

from app import create_app
from app.core.extensions import db
from app.reports.service import get_daily_report, get_weekly_report


def test_daily_report_empty():
    app = create_app()

    with app.app_context():
        db.create_all()

        report = get_daily_report(999999, date.today())

        assert report["calories"] == 0
        assert report["protein"] == 0
        assert report["carbohydrates"] == 0
        assert report["fats"] == 0
        assert report["meal_count"] == 0


def test_weekly_report_returns_seven_days():
    app = create_app()

    with app.app_context():
        db.create_all()

        report = get_weekly_report(999999)

        assert len(report) == 7