from app.core.extensions import db
from app.profile.models import Profile


def create_profile(
    user_id,
    age,
    sex,
    height_cm,
    weight_kg,
    activity_level,
    goal
):
    daily_calorie_target = calculate_daily_calorie_target(
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal
    )

    profile = Profile(
        user_id=user_id,
        age=age,
        sex=sex,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_level=activity_level,
        goal=goal,
        daily_calorie_target=daily_calorie_target
    )

    db.session.add(profile)
    db.session.commit()

    bmi = calculate_bmi(height_cm, weight_kg)

    warning = None

    if goal.lower() in ["gain_0.5", "gain_1"]:
        warning = get_weight_gain_warning(bmi)

    return profile, bmi, warning


def calculate_bmi(height_cm, weight_kg):
    height_m = height_cm / 100

    bmi = weight_kg / (height_m ** 2)

    return round(bmi, 2)


def get_weight_gain_warning(bmi):
    if bmi < 18.5:
        return (
            "Your BMI is below the standard healthy-weight range. "
            "Consider discussing your weight-gain goal with a healthcare professional."
        )

    if bmi < 25:
        return (
            "Your BMI is currently within the standard healthy-weight range. "
            "Consider whether intentional weight gain is appropriate for your goals."
        )

    return (
        "Your BMI is above the standard healthy-weight range. "
        "Consider discussing your weight-gain goal with a healthcare professional."
    )


def calculate_daily_calorie_target(
    age,
    sex,
    height_cm,
    weight_kg,
    activity_level,
    goal
):
    if sex.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }

    maintenance_calories = bmr * activity_multipliers.get(
        activity_level.lower(),
        1.2
    )

    goal_adjustments = {
        "lose_0.5": -550,
        "lose_1": -1100,
        "maintain": 0,
        "gain_0.5": 550,
        "gain_1": 1100
    }

    daily_target = maintenance_calories + goal_adjustments.get(
        goal.lower(),
        0
    )

    if sex.lower() == "female":
        minimum_calories = 1200
    else:
        minimum_calories = 1500

    daily_target = max(daily_target, minimum_calories)

    return round(daily_target)

def update_profile(
    profile,
    age,
    sex,
    height_cm,
    weight_kg,
    activity_level,
    goal
):
    daily_calorie_target = calculate_daily_calorie_target(
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal
    )

    profile.age = age
    profile.sex = sex
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.goal = goal
    profile.daily_calorie_target = daily_calorie_target

    db.session.commit()

    bmi = calculate_bmi(height_cm, weight_kg)

    warning = None

    if goal.lower() in ["gain_0.5", "gain_1"]:
        warning = get_weight_gain_warning(bmi)

    return profile, bmi, warning

def calculate_macro_targets(daily_calorie_target):
    protein = (daily_calorie_target * 0.21) / 4
    carbohydrates = (daily_calorie_target * 0.54) / 4
    fats = (daily_calorie_target * 0.25) / 9

    return (
        round(protein, 1),
        round(carbohydrates, 1),
        round(fats, 1)
    )