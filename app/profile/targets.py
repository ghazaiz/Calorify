def calculate_macro_targets(daily_calorie_target):
    protein = (daily_calorie_target * 0.21) / 4
    carbohydrates = (daily_calorie_target * 0.54) / 4
    fats = (daily_calorie_target * 0.25) / 9

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
