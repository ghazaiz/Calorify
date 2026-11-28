from datetime import date, timedelta

from sqlalchemy import func

from app.meals.models import Meal


NUTRIENT_TOTALS = (
    func.sum(Meal.calories),
    func.sum(Meal.protein),
    func.sum(Meal.carbohydrates),
    func.sum(Meal.fats),
)


def _totals(values):
    return {
        nutrient: round(value or 0, 1)
        for nutrient, value in zip(
            ("calories", "protein", "carbohydrates", "fats"), values
        )
    }


def get_daily_report(user_id, report_date=None):
    report_date = report_date or date.today()
    row = Meal.query.with_entities(*NUTRIENT_TOTALS, func.count()).filter_by(
        user_id=user_id, date=report_date
    ).one()
    return {
        "date": report_date.isoformat(),
        **_totals(row[:4]),
        "meal_count": row[4],
    }


def get_weekly_report(user_id, end_date=None, *, include_counts=False):
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)
    rows = Meal.query.with_entities(Meal.date, *NUTRIENT_TOTALS, func.count(Meal.meal_id)).filter(
        Meal.user_id == user_id,
        Meal.date.between(start_date, end_date),
    ).group_by(Meal.date)
    totals_by_date = {row[0]: (_totals(row[1:5]), row[5]) for row in rows}
    empty_totals = _totals((0, 0, 0, 0))
    report = []
    for offset in range(7):
        day = start_date + timedelta(days=offset)
        totals, count = totals_by_date.get(day, (empty_totals, 0))
        entry = {"date": day.isoformat(), **totals}
        if include_counts:
            entry["meal_count"] = count
        report.append(entry)
    return report
