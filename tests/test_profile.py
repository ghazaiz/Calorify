from app.profile.service import (
    calculate_bmi,
    calculate_macro_targets,
    calculate_daily_calorie_target
)


def test_calculate_bmi():
    bmi = calculate_bmi(170, 70)

    assert bmi == 24.22


def test_calculate_macro_targets():
    protein, carbs, fats = calculate_macro_targets(2400)

    assert protein == 126.0
    assert carbs == 324.0
    assert fats == 66.7


def test_calculate_daily_calorie_target():
    calories = calculate_daily_calorie_target(
        20,
        "female",
        170,
        70,
        "moderate",
        "maintain"
    )

    assert calories > 1200