from datetime import date, timedelta

from app.meals.models import Meal


def get_daily_report(user_id, report_date=None):
    report_date = report_date or date.today()

    meals = Meal.query.filter_by(
        user_id=user_id,
        date=report_date
    ).all()

    return {
        "date": report_date.isoformat(),
        "calories": round(sum(meal.calories for meal in meals), 1),
        "protein": round(sum(meal.protein for meal in meals), 1),
        "carbohydrates": round(
            sum(meal.carbohydrates for meal in meals), 1
        ),
        "fats": round(sum(meal.fats for meal in meals), 1),
        "meal_count": len(meals)
    }


def get_weekly_report(user_id, end_date=None):
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)

    meals = Meal.query.filter(
        Meal.user_id == user_id,
        Meal.date >= start_date,
        Meal.date <= end_date
    ).all()

    daily_data = []

    for i in range(7):
        current_date = start_date + timedelta(days=i)

        day_meals = [
            meal for meal in meals
            if meal.date == current_date
        ]

        daily_data.append({
            "date": current_date.isoformat(),
            "calories": round(
                sum(meal.calories for meal in day_meals), 1
            ),
            "protein": round(
                sum(meal.protein for meal in day_meals), 1
            ),
            "carbohydrates": round(
                sum(meal.carbohydrates for meal in day_meals), 1
            ),
            "fats": round(
                sum(meal.fats for meal in day_meals), 1
            )
        })

    return daily_data