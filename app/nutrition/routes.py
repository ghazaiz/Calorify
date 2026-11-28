import re

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user

from app.core.exceptions import NutritionProviderError
from app.core.http import wants_json
from app.nutrition.meal_query import BIRYANI, CHICKEN_CUTS, biryani_items, parse_meal, valid_amount
from app.nutrition.portions import CORE_NUTRIENTS, MAX_QUANTITY, MIN_QUANTITY, number, portion_options
from app.nutrition.service import label_result, search_food, search_meal
from app.profile.models import Profile
from app.reports.service import get_daily_report


nutrition_bp = Blueprint("nutrition", __name__, url_prefix="/nutrition")

# Embedded quantities otherwise look like food-name tokens to providers.
EMBEDDED_AMOUNT = re.compile(
    r"^\d+(?:\.\d+)?\s+|\b\d+(?:\.\d+)?\s*(?:g|kg|grams?|ml|cups?|oz|pieces?|servings?)\b",
    re.I,
)


def _page(**context):
    if not current_user.is_authenticated:
        return render_template("nutrition/guest.html", **context)
    profile = Profile.query.filter_by(user_id=current_user.user_id).first()
    return render_template(
        "nutrition/search.html", today=get_daily_report(current_user.user_id),
        calorie_goal=profile.daily_calorie_target if profile else 0,
        **context,
    )


@nutrition_bp.get("/guest")
def guest_search():
    return render_template("nutrition/guest.html")


def _measured_result(mode, name):
    serving = number(request.args.get("serving_grams"))
    if not valid_amount(serving):
        raise ValueError("Enter the weight of the portion you ate in grams.")
    if mode == "label":
        basis = number(request.args.get("label_grams"))
        if not valid_amount(basis):
            raise ValueError("Enter the weight the label values apply to, such as 100 g.")
        nutrients = {}
        for key in CORE_NUTRIENTS:
            raw_value = request.args.get(f"label_{key}", "").strip()
            value = number(raw_value)
            if (raw_value or key == "calories") and (value is None or value > MAX_QUANTITY):
                raise ValueError(f"Enter a valid label value for {key}.")
            nutrients[key] = value
        return label_result(name, basis, serving, nutrients)

    batch = number(request.args.get("batch_grams"))
    if not valid_amount(batch) or serving > batch:
        raise ValueError("Enter the finished batch weight in grams. It must be at least the weight of your portion.")
    ingredients = request.args.get("ingredients", "").strip()
    if not ingredients or len(ingredients) > 2000:
        raise ValueError("Enter your ingredients in 2,000 characters or fewer.")
    items = [
        item for line in ingredients.splitlines() if line.strip()
        for item in parse_meal(line, recipe=True)
    ]
    if len(items) > 20 or any(unit != "g" for _, _, unit in items):
        raise ValueError("Enter up to 20 ingredients, each with a weight in grams.")
    return search_meal(items, name=name, yield_grams=batch, serving_grams=serving)


@nutrition_bp.get("/search")
def search():
    mode = request.args.get("mode")
    sentence = request.args.get("sentence", "").strip()
    food_name = request.args.get("food", "").strip()

    def problem(message, status, html_message=None, **context):
        if wants_json():
            return jsonify({"message": message, **context}), status
        return _page(searched_food=food_name, error=html_message or message, **context), status

    if not food_name and not sentence:
        if "food" not in request.args and "sentence" not in request.args and not wants_json():
            return _page()
        return problem("Please enter a food name", 400)
    if len(sentence) > 500:
        return problem("Keep your meal description to 500 characters or fewer", 400)
    if len(food_name) > 200:
        return problem("Food names must be 200 characters or fewer", 400)
    if not mode and EMBEDDED_AMOUNT.search(food_name):
        return problem("Enter the food name and set its amount separately", 400)

    raw = request.args.get("quantity") or request.args.get("servings")
    unit = request.args.get("unit") or ("serving" if request.args.get("servings") else "g")
    quantity = number(raw)
    if raw and (quantity is None or not MIN_QUANTITY <= quantity <= MAX_QUANTITY):
        return problem(f"Enter an amount from {MIN_QUANTITY} to {MAX_QUANTITY:,}", 400)
    if unit not in {"g", "ml", "serving", "piece"}:
        return problem("Select grams, milliliters, servings, or pieces", 400)

    try:
        meat_weight = request.args.get("meat_weight")
        if mode in {"label", "recipe"}:
            if not food_name:
                return problem("Please enter a food or recipe name", 400)
            result = _measured_result(mode, food_name)
            if wants_json():
                return jsonify(result)
            return _page(result=result)
        if sentence:
            items = parse_meal(sentence)
        elif meat_weight:
            if unit != "g" or not BIRYANI.search(food_name):
                return problem("Separate chicken weights are available for biryani measured in grams.", 400)
            items = biryani_items(quantity, number(meat_weight), request.args.get("chicken_cut", "breast"))
        else:
            items = [(food_name, quantity, unit if raw else None)]
        if any(not name for name, _, _ in items):
            return problem("Please enter a food name", 400)
        if len(items) > 8:
            return problem("Check up to eight foods at a time.", 400)
        if len(items) == 1:
            name, amount, amount_unit = items[0]
            result = search_food(name, amount, unit=amount_unit)
        else:
            split_biryani = (
                len(items) == 2 and items[0][0] == "Biryani rice"
                and items[1][0] in CHICKEN_CUTS.values()
            )
            result = search_meal(items, name="Chicken biryani" if split_biryani else None)
    except ValueError as error:
        return problem(str(error), 400)
    except LookupError as error:
        return problem(str(error), 404)
    except NutritionProviderError:
        return problem("Nutrition databases are unavailable. Try again shortly.", 503)
    except Exception:
        current_app.logger.exception("Nutrition search failed")
        return problem("Nutrition search is temporarily unavailable. Try again shortly.", 503)

    if result is None:
        return problem(
            "Food not found", 404,
            "No matching nutrition record was found. Try a more specific food or brand, or enter the measured ingredients in a sentence.",
        )

    if result.get("portion_unavailable"):
        return problem(
            "This record cannot convert the requested amount. Use one of the units shown below.",
            422, result=result,
        )
    if wants_json():
        return jsonify(result)
    return _page(searched_food=food_name, result=result)


@nutrition_bp.app_context_processor
def portion_helpers():
    return {"portion_options": portion_options, "max_nutrition_quantity": MAX_QUANTITY}
