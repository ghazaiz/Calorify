from datetime import date

from app.core.extensions import db
from app.meals.models import Meal


ALLOWED_MEAL_TYPES = {
    "breakfast",
    "lunch",
    "dinner",
    "snack"
}


def add_meal(
    user_id,
    food_name,
    meal_type,
    quantity,
    serving_unit,
    calories,
    protein,
    carbohydrates,
    fats,
    meal_date=None
):
    if meal_type.lower() not in ALLOWED_MEAL_TYPES:
        return None

    meal = Meal(
        user_id=user_id,
        food_name=food_name,
        meal_type=meal_type.lower(),
        quantity=quantity,
        serving_unit=serving_unit,
        calories=calories,
        protein=protein,
        carbohydrates=carbohydrates,
        fats=fats,
        date=meal_date or date.today()
    )

    db.session.add(meal)
    db.session.commit()

    return meal


def get_user_meals(user_id):
    return Meal.query.filter_by(
        user_id=user_id
    ).order_by(
        Meal.date.desc(),
        Meal.created_at.desc()
    ).all()


def get_user_meal(meal_id, user_id):
    return Meal.query.filter_by(
        meal_id=meal_id,
        user_id=user_id
    ).first()


def update_meal(
    meal,
    food_name,
    meal_type,
    quantity,
    serving_unit,
    calories,
    protein,
    carbohydrates,
    fats,
    meal_date=None
):
    if meal_type.lower() not in ALLOWED_MEAL_TYPES:
        return None

    meal.food_name = food_name
    meal.meal_type = meal_type.lower()
    meal.quantity = quantity
    meal.serving_unit = serving_unit
    meal.calories = calories
    meal.protein = protein
    meal.carbohydrates = carbohydrates
    meal.fats = fats

    if meal_date:
        meal.date = meal_date

    db.session.commit()

    return meal


def delete_meal(meal):
    db.session.delete(meal)
    db.session.commit()