from flask import Blueprint, request, jsonify
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

    if user_profile is None:
        return jsonify({
            "message": "No profile found"
        }), 404

    return jsonify({
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
    }), 200


@profile_bp.route("/", methods=["POST"])
@login_required
def create_user_profile():
    data = request.get_json()

    age = data.get("age")
    sex = data.get("sex")
    height_cm = data.get("height_cm")
    weight_kg = data.get("weight_kg")
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

    profile, bmi, warning = create_profile(
        current_user.user_id,
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal
    )

    return jsonify({
        "message": "Profile created successfully",
        "daily_calorie_target": profile.daily_calorie_target,
        "protein_target": profile.protein_target,
        "carbohydrates_target": profile.carbohydrates_target,
        "fats_target": profile.fats_target,
        "bmi": bmi,
        "warning": warning
    }), 201


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

    age = data.get("age")
    sex = data.get("sex")
    height_cm = data.get("height_cm")
    weight_kg = data.get("weight_kg")
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
        goal
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