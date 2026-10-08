from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

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


@meals_bp.route("/", methods=["GET"])
@login_required
def get_meals():
    meals = get_user_meals(current_user.user_id)

    return jsonify({
        "meals": [meal_to_dict(meal) for meal in meals]
    }), 200


@meals_bp.route("/", methods=["POST"])
@login_required
def create_meal():
    data = request.get_json()

    required_fields = [
        "food_name",
        "meal_type",
        "quantity",
        "serving_unit",
        "calories",
        "protein",
        "carbohydrates",
        "fats"
    ]

    if not all(field in data for field in required_fields):
        return jsonify({
            "message": "All meal fields are required"
        }), 400

    meal_date = None

    if data.get("date"):
        try:
            meal_date = datetime.strptime(
                data["date"],
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({
                "message": "Date must be in YYYY-MM-DD format"
            }), 400

    meal = add_meal(
        current_user.user_id,
        data["food_name"],
        data["meal_type"],
        data["quantity"],
        data["serving_unit"],
        data["calories"],
        data["protein"],
        data["carbohydrates"],
        data["fats"],
        meal_date
    )

    if meal is None:
        return jsonify({
            "message": "Invalid meal type. Use breakfast, lunch, dinner, or snack"
        }), 400

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

    data = request.get_json()

    required_fields = [
        "food_name",
        "meal_type",
        "quantity",
        "serving_unit",
        "calories",
        "protein",
        "carbohydrates",
        "fats"
    ]

    if not all(field in data for field in required_fields):
        return jsonify({
            "message": "All meal fields are required"
        }), 400

    meal_date = None

    if data.get("date"):
        try:
            meal_date = datetime.strptime(
                data["date"],
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({
                "message": "Date must be in YYYY-MM-DD format"
            }), 400

    updated_meal = update_meal(
        meal,
        data["food_name"],
        data["meal_type"],
        data["quantity"],
        data["serving_unit"],
        data["calories"],
        data["protein"],
        data["carbohydrates"],
        data["fats"],
        meal_date
    )

    if updated_meal is None:
        return jsonify({
            "message": "Invalid meal type. Use breakfast, lunch, dinner, or snack"
        }), 400

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