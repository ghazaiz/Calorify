from math import isfinite
from datetime import date, datetime, timedelta

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

from app.core.exceptions import InvalidMealTypeError
from app.core.http import wants_json
from app.meals.service import (
    add_meal,
    get_user_meals,
    get_user_meal,
    update_meal,
    delete_meal
)


meals_bp = Blueprint(
    "meals",
    __name__,
    url_prefix="/meals"
)

def meal_to_dict(meal):
    return {
        "meal_id": meal.meal_id,
        "food_name": meal.food_name,
        "meal_type": meal.meal_type,
        "quantity": meal.quantity,
        "serving_unit": meal.serving_unit,
        "calories": meal.calories,
        "protein": meal.protein,
        "carbohydrates": meal.carbohydrates,
        "fats": meal.fats,
        "date": meal.date.isoformat()
    }


def _meal_input():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("A JSON object is required")

    text_fields = {"food_name": 200, "meal_type": 20, "serving_unit": 50}
    numeric_fields = ("quantity", "calories", "protein", "carbohydrates", "fats")
    if any(field not in data for field in (*text_fields, *numeric_fields)):
        raise ValueError("All meal fields are required")

    values = {}
    for field, max_length in text_fields.items():
        value = data[field]
        if not isinstance(value, str) or not 0 < len(value.strip()) <= max_length:
            raise ValueError(f"{field} must contain 1 to {max_length} characters")
        values[field] = value.strip()

    for field in numeric_fields:
        value = data[field]
        if isinstance(value, bool):
            raise ValueError("Quantity and nutrition values must be numbers")
        try:
            values[field] = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Quantity and nutrition values must be numbers") from None
        if not isfinite(values[field]):
            raise ValueError("Quantity and nutrition values must be finite")

    if values["quantity"] <= 0 or any(values[field] < 0 for field in numeric_fields[1:]):
        raise ValueError("Quantity must be positive and nutrition values cannot be negative")

    raw_date = data.get("date")
    if raw_date is not None and raw_date != "":
        try:
            values["meal_date"] = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise ValueError("Date must be in YYYY-MM-DD format") from None
    return values


@meals_bp.route("/", methods=["GET"])
@login_required
def get_meals():
    meals = get_user_meals(current_user.user_id)

    if not wants_json():
        today = date.today()
        meals_view = []

        for meal in meals:
            meal_data = meal_to_dict(meal)

            if meal.date == today:
                meal_data["date_display"] = "Today"
            elif meal.date == today - timedelta(days=1):
                meal_data["date_display"] = "Yesterday"
            else:
                meal_data["date_display"] = (
                    f"{meal.date.day} {meal.date.strftime('%b')}"
                )

            meals_view.append(meal_data)

        return render_template(
            "meals/meals.html",
            today_iso=today.isoformat(),
            meals=meals_view
        )

    return jsonify({
        "meals": [meal_to_dict(meal) for meal in meals]
    }), 200


@meals_bp.route("/", methods=["POST"])
@login_required
def create_meal():
    try:
        values = _meal_input()
        meal = add_meal(current_user.user_id, **values)
    except (ValueError, InvalidMealTypeError) as error:
        return jsonify({"message": str(error)}), 400

    return jsonify({
        "message": "Meal added successfully",
        "meal": meal_to_dict(meal)
    }), 201


@meals_bp.route("/<int:meal_id>", methods=["PUT"])
@login_required
def edit_meal(meal_id):
    meal = get_user_meal(
        meal_id,
        current_user.user_id
    )

    if meal is None:
        return jsonify({
            "message": "Meal not found"
        }), 404

    try:
        updated_meal = update_meal(meal, **_meal_input())
    except (ValueError, InvalidMealTypeError) as error:
        return jsonify({"message": str(error)}), 400

    return jsonify({
        "message": "Meal updated successfully",
        "meal": meal_to_dict(updated_meal)
    }), 200


@meals_bp.route("/<int:meal_id>", methods=["DELETE"])
@login_required
def remove_meal(meal_id):
    meal = get_user_meal(
        meal_id,
        current_user.user_id
    )

    if meal is None:
        return jsonify({
            "message": "Meal not found"
        }), 404

    delete_meal(meal)

    return jsonify({
        "message": "Meal deleted successfully"
    }), 200