from math import isfinite

from app.core.extensions import db
from app.profile.models import Profile
from app.profile.targets import calculate_daily_calorie_target, calculate_macro_targets


def calculate_bmi(height_cm, weight_kg):
    height_m = height_cm / 100

    bmi = weight_kg / (height_m * height_m)

    return round(bmi, 2)


def bmi_category(bmi):
    """Standard adult BMI category for a BMI value."""
    if bmi < 18.5:
        return "Underweight"

    if bmi < 25:
        return "Normal weight"

    if bmi < 30:
        return "Overweight"

    return "Obesity"


def get_bmi_summary(profile):
    """BMI computed from the profile's latest saved height and weight.

    Returns None when the profile is missing or its measurements are
    absent or invalid, so callers can show a prompt instead of
    crashing. BMI is never stored, so it can never go stale.
    """
    if profile is None:
        return None

    try:
        height_cm = float(profile.height_cm)
        weight_kg = float(profile.weight_kg)
    except (TypeError, ValueError):
        return None

    if not all(isfinite(value) and value > 0 for value in (height_cm, weight_kg)):
        return None

    bmi = calculate_bmi(height_cm, weight_kg)

    return {
        "value": bmi,
        "category": bmi_category(bmi),
        "height_cm": height_cm,
        "weight_kg": weight_kg
    }


def create_profile(
    user_id,
    age,
    sex,
    height_cm,
    weight_kg,
    activity_level,
    goal,
    weekly_loss=0.5
):
    bmi = calculate_bmi(
        height_cm,
        weight_kg
    )

    warning = None

    if bmi < 18.5:
        warning = "Your BMI is below the normal range."
    elif bmi >= 30:
        warning = "Your BMI is in the obesity range."

    profile = Profile(
        user_id=user_id,
        age=age,
        sex=sex,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_level=activity_level,
        goal=goal,
        weekly_loss=weekly_loss,
    )

    db.session.add(profile)
    db.session.commit()

    return profile, bmi, warning


def update_profile(
    profile,
    age,
    sex,
    height_cm,
    weight_kg,
    activity_level,
    goal,
    weekly_loss=0.5
):
    profile.age = age
    profile.sex = sex
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.goal = goal
    profile.weekly_loss = weekly_loss

    db.session.commit()

    bmi = calculate_bmi(
        height_cm,
        weight_kg
    )

    warning = None

    if bmi < 18.5:
        warning = "Your BMI is below the normal range."
    elif bmi >= 30:
        warning = "Your BMI is in the obesity range."

    return profile, bmi, warning