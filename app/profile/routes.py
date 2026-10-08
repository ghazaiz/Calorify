from flask import Blueprint, request, jsonify, render_template, redirect
from flask_login import login_required, current_user

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