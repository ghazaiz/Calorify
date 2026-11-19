from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user

from app.core.http import wants_json
from app.nutrition.service import search_food
from app.profile.models import Profile
from app.reports.service import get_daily_report


nutrition_bp = Blueprint(
    "nutrition",
    __name__,
    url_prefix="/nutrition"
)


def _search_template():
    """Guests get the standalone guest page, members the app page."""
    if current_user.is_authenticated:
        return "nutrition/search.html"

    return "nutrition/guest.html"


def _day_context():
    """Today's totals and goals so the page can show how a food fits."""
    if not current_user.is_authenticated:
        return {}

    profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    return {
        "today": get_daily_report(current_user.user_id),
        "calorie_goal": profile.daily_calorie_target if profile else 0,
        "fats_goal": profile.fats_target if profile else 0
    }


@nutrition_bp.route("/guest", methods=["GET"])
def guest_search():
    return render_template("nutrition/guest.html")


@nutrition_bp.route("/search", methods=["GET"])
def search():
    food_name = request.args.get("food")

    if not food_name:
        if not wants_json():
            return render_template(_search_template(), **_day_context())
        return jsonify({
            "message": "Please enter a food name"
        }), 400

    quantity = request.args.get(
        "quantity",
        type=float
    )

    meat_weight = request.args.get(
        "meat_weight",
        type=float
    )

    if quantity is not None and quantity <= 0:
        return jsonify({
            "message": "Quantity must be greater than 0"
        }), 400

    if meat_weight is not None and meat_weight <= 0:
        return jsonify({
            "message": "Meat weight must be greater than 0"
        }), 400

    try:
        result = search_food(
            food_name,
            quantity,
            meat_weight
        )

        if result is None:
            if not wants_json():
                return render_template(
                    _search_template(),
                    searched_food=food_name,
                    error=f"We couldn't find nutrition information for “{food_name}”. Try another food.",
                    **_day_context()
                ), 404
            return jsonify({
                "message": "Food not found"
            }), 404

        if not wants_json():
            return render_template(
                _search_template(),
                result=result,
                searched_food=food_name,
                **_day_context()
            )

        return jsonify(result), 200

    except Exception as error:
        if not wants_json():
            return render_template(
                _search_template(),
                searched_food=food_name,
                error="The nutrition service is temporarily unavailable. Please try again.",
                **_day_context()
            ), 503
        return jsonify({
            "message": "Unable to get nutrition information",
            "error": str(error)
        }), 500
