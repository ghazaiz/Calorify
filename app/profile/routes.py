from math import isfinite

from flask import Blueprint, request, jsonify, render_template, redirect
from flask_login import login_required, current_user, logout_user

from app.authentication.service import hash_password, verify_password
from app.core.extensions import db
from app.meals.models import Meal
from app.profile.models import Profile
from app.profile.service import create_profile, update_profile


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile"
)


def _profile_input(data):
    try:
        age = int(str(data.get("age")))
        height = float(str(data.get("height_cm")))
        weight = float(str(data.get("weight_kg")))
        weekly_loss = float(str(data.get("weekly_loss", 0.5)))
    except ValueError:
        raise ValueError("Please enter valid numbers for age, height, weight and weekly loss") from None

    if not 1 <= age <= 120:
        raise ValueError("Age must be between 1 and 120")
    if not all(isfinite(value) and value >= 1 for value in (height, weight)):
        raise ValueError("Height and weight must be finite and at least 1")
    max_calorie_target = (10 * weight + 6.25 * height) * 1.725 + 300
    if max_calorie_target > 2_147_483_647:
        raise ValueError("Height or weight is too large")
    if weekly_loss not in (0.5, 1):
        raise ValueError("Weekly weight loss must be 0.5 or 1 kg")

    choices = {
        "sex": ("male", "female"),
        "activity_level": ("sedentary", "light", "moderate", "active"),
        "goal": ("lose", "maintain", "gain"),
    }
    values = {}
    for field, allowed in choices.items():
        raw = data.get(field)
        value = raw.strip().lower() if isinstance(raw, str) else None
        if value not in allowed:
            raise ValueError(f"Select a valid {field.replace('_', ' ')}")
        values[field] = value

    return {
        **values,
        "age": age,
        "height_cm": height,
        "weight_kg": weight,
        "weekly_loss": weekly_loss,
    }


@profile_bp.route("/", methods=["GET"])
@login_required
def profile():

    user_profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    return render_template(
        "profile/profile.html",
        profile=user_profile
    )


@profile_bp.route("/", methods=["POST"])
@login_required
def create_user_profile():

    existing_profile = Profile.query.filter_by(user_id=current_user.user_id).first()
    try:
        values = _profile_input(request.form)
    except ValueError as error:
        return render_template(
            "profile/profile.html", profile=existing_profile, error=str(error)
        )

    if existing_profile:
        update_profile(existing_profile, **values)
    else:
        create_profile(current_user.user_id, **values)

    return redirect("/reports/dashboard?profile_saved=1")


@profile_bp.route("/", methods=["PUT"])
@login_required
def update_user_profile():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "A JSON object is required"
        }), 400

    user_profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    if user_profile is None:
        return jsonify({
            "message": "Profile not found"
        }), 404

    try:
        values = _profile_input(data)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400

    profile, bmi, warning = update_profile(user_profile, **values)

    return jsonify({
        "message": "Profile updated successfully",
        "daily_calorie_target": profile.daily_calorie_target,
        "protein_target": profile.protein_target,
        "carbohydrates_target": profile.carbohydrates_target,
        "fats_target": profile.fats_target,
        "bmi": bmi,
        "warning": warning
    }), 200

@profile_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():

    data = request.form

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    user_profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    if not verify_password(
        current_password,
        current_user.password_hash
    ):
        return render_template(
            "profile/profile.html",
            profile=user_profile,
            password_error="Current password is incorrect"
        )

    if len(new_password) < 8:
        return render_template(
            "profile/profile.html",
            profile=user_profile,
            password_error="New password must be at least 8 characters long"
        )

    current_user.password_hash = hash_password(new_password)
    db.session.commit()

    return render_template(
        "profile/profile.html",
        profile=user_profile,
        password_success="Password updated successfully"
    )


@profile_bp.route("/export", methods=["GET"])
@login_required
def export_data():

    user_profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    meals = Meal.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Meal.date).all()

    payload = {
        "account": {
            "username": current_user.username,
            "email": current_user.email,
            "member_since": current_user.created_at.isoformat()
        },
        "profile": {
            "age": user_profile.age,
            "sex": user_profile.sex,
            "height_cm": user_profile.height_cm,
            "weight_kg": user_profile.weight_kg,
            "activity_level": user_profile.activity_level,
            "goal": user_profile.goal,
            "weekly_loss": user_profile.weekly_loss,
            "daily_calorie_target": user_profile.daily_calorie_target,
            "protein_target": user_profile.protein_target,
            "carbohydrates_target": user_profile.carbohydrates_target,
            "fats_target": user_profile.fats_target
        } if user_profile else None,
        "meals": [
            {
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
            for meal in meals
        ]
    }

    response = jsonify(payload)
    response.headers["Content-Disposition"] = (
        "attachment; filename=calorify-data.json"
    )

    return response


@profile_bp.route("/delete", methods=["POST"])
@login_required
def delete_account():

    user = current_user._get_current_object()

    Meal.query.filter_by(user_id=user.user_id).delete()
    Profile.query.filter_by(user_id=user.user_id).delete()

    db.session.delete(user)
    db.session.commit()
    logout_user()

    return redirect("/auth/register")
