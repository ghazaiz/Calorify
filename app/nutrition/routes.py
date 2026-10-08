from flask import Blueprint, request, jsonify, render_template

from app.nutrition.service import search_food


nutrition_bp = Blueprint(
    "nutrition",
    __name__,
    url_prefix="/nutrition"
)


@nutrition_bp.route("/guest", methods=["GET"])
def guest_search():
    return render_template("nutrition/guest.html")

@nutrition_bp.route("/search", methods=["GET"])
def search():
    food_name = request.args.get("food")

    if not food_name:
        if request.accept_mimetypes.best == "text/html":
            return render_template("nutrition/search.html")
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
            if request.accept_mimetypes.best == "text/html":
                return render_template(
                    "nutrition/search.html",
                    searched_food=food_name,
                    error=f"We couldn't find nutrition information for “{food_name}”. Try another food."
                ), 404
            return jsonify({
                "message": "Food not found"
            }), 404

        if request.accept_mimetypes.best == "text/html":
            return render_template(
                "nutrition/search.html",
                result=result,
                searched_food=food_name
            )

        return jsonify(result), 200

    except Exception as error:
        if request.accept_mimetypes.best == "text/html":
            return render_template(
                "nutrition/search.html",
                searched_food=food_name,
                error="The nutrition service is temporarily unavailable. Please try again."
            ), 503
        return jsonify({
            "message": "Unable to get nutrition information",
            "error": str(error)
        }), 500