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

def test_reports_total_only_the_requested_users_meals():
    from app.authentication.service import register_user
    from app.meals.service import add_meal, get_user_meals

    app = create_app()
    with app.app_context():
        user = register_user("reports", "reports@example.com", "password123")
        other = register_user("other", "other@example.com", "password123")
        end_date = date(2026, 4, 10)
        add_meal(user.user_id, "Oats", "breakfast", 100, "g", 100.4, 3, 15, 2, end_date)
        add_meal(user.user_id, "Egg", "lunch", 50, "g", 70.4, 6, 0, 5, end_date)
        add_meal(user.user_id, "Rice", "lunch", 100, "g", 130, 3, 28, 0, date(2026, 4, 3))
        add_meal(other.user_id, "Bread", "snack", 100, "g", 200, 5, 30, 2, end_date)

        daily = get_daily_report(user.user_id, end_date)
        weekly = get_weekly_report(user.user_id, end_date)
        assert daily["meal_count"] == 2
        assert daily["calories"] == 170.8
        assert weekly[-1] == {key: value for key, value in daily.items() if key != "meal_count"}
        assert all(day["calories"] == 0 for day in weekly[:-1])
        assert len(get_user_meals(user.user_id, end_date)) == 2
