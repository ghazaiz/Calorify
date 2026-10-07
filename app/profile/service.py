from app.core.extensions import db
from app.profile.models import Profile


def calculate_bmi(height_cm, weight_kg):
    height_m = height_cm / 100

    bmi = weight_kg / (height_m * height_m)

    return round(bmi, 2)


def calculate_macro_targets(daily_calorie_target):
    protein = (daily_calorie_target * 0.30) / 4
    carbohydrates = (daily_calorie_target * 0.40) / 4
    fats = (daily_calorie_target * 0.30) / 9

    return (
        round(protein, 1),
        round(carbohydrates, 1),
        round(fats, 1)
    )


def calculate_daily_calorie_target(
    age,
    sex,
    height_cm,
    weight_kg,
    activity_level,
    goal,
    weekly_loss=0.5
):
    if sex.lower() == "male":
        bmr = (
            (10 * weight_kg)
            + (6.25 * height_cm)
            - (5 * age)
            + 5
        )
    else:
        bmr = (
            (10 * weight_kg)
            + (6.25 * height_cm)
            - (5 * age)
            - 161
        )

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725
    }

    activity_multiplier = activity_multipliers.get(
        activity_level.lower(),
        1.2
    )

    calories = bmr * activity_multiplier

    if goal.lower() == "lose":
        if weekly_loss == 1:
            calories -= 1100
        else:
            calories -= 550

    elif goal.lower() == "gain":
        calories += 300

    return max(round(calories), 1200)


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
    daily_calorie_target = calculate_daily_calorie_target(
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal,
        weekly_loss
    )

    protein, carbohydrates, fats = calculate_macro_targets(
        daily_calorie_target
    )

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
        daily_calorie_target=daily_calorie_target,
        protein_target=protein,
        carbohydrates_target=carbohydrates,
        fats_target=fats
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
    daily_calorie_target = calculate_daily_calorie_target(
        age,
        sex,
        height_cm,
        weight_kg,
        activity_level,
        goal,
        weekly_loss
    )

    protein, carbohydrates, fats = calculate_macro_targets(
        daily_calorie_target
    )

    profile.age = age
    profile.sex = sex
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.goal = goal
    profile.daily_calorie_target = daily_calorie_target
    profile.protein_target = protein
    profile.carbohydrates_target = carbohydrates
    profile.fats_target = fats

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