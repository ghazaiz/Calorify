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

    data = request.form

    age_text = data.get("age")
    height_text = data.get("height_cm")
    weight_text = data.get("weight_kg")

    sex = data.get("sex")
    activity_level = data.get("activity_level")
    goal = data.get("goal")

    try:
        age = int(age_text)
        height_cm = float(height_text)
        weight_kg = float(weight_text)
        weekly_loss = float(
            data.get("weekly_loss", 0.5)
        )
    except (TypeError, ValueError):
        return render_template(
            "profile/profile.html",
            error="Please enter valid numbers for age, height and weight"
        )

    if not all([
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal
    ]):
        return render_template(
            "profile/profile.html",
            error="All profile fields are required"
        )

    existing_profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    if existing_profile:

        update_profile(
            existing_profile,
            age,
            sex,
            height_cm,
            weight_kg,
            activity_level,
            goal,
            weekly_loss
        )

    else:

        create_profile(
            current_user.user_id,
            age,
            sex,
            height_cm,
            weight_kg,
            activity_level,
            goal,
            weekly_loss
        )

    return redirect("/reports/dashboard")

@profile_bp.route("/", methods=["PUT"])
@login_required
def update_user_profile():

    data = request.get_json()

    user_profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    if user_profile is None:
        return jsonify({
            "message": "Profile not found"
        }), 404

    try:
        age = int(data.get("age"))
        height_cm = float(data.get("height_cm"))
        weight_kg = float(data.get("weight_kg"))
        weekly_loss = float(data.get("weekly_loss", 0.5))
    except (TypeError, ValueError):
        return jsonify({
            "message": "Please enter valid numbers"
        }), 400

    sex = data.get("sex")
    activity_level = data.get("activity_level")
    goal = data.get("goal")

    if not all([
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal
    ]):
        return jsonify({
            "message": "All profile fields are required"
        }), 400

    profile, bmi, warning = update_profile(
        user_profile,
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal,
        weekly_loss
    )

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

    logout_user()

    db.session.delete(user)
    db.session.commit()

    return redirect("/auth/register")
