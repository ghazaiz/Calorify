from types import SimpleNamespace

from app import create_app
from app.core.extensions import db
from app.profile.models import Profile
from app.profile.service import (
    bmi_category,
    calculate_bmi,
    calculate_daily_calorie_target,
    calculate_macro_targets,
    get_bmi_summary
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


# ---------------------------------------------------------------------------
# BMI helpers
# ---------------------------------------------------------------------------

def test_bmi_category_boundaries():
    assert bmi_category(18.4) == "Underweight"
    assert bmi_category(18.5) == "Normal weight"
    assert bmi_category(24.9) == "Normal weight"
    assert bmi_category(25) == "Overweight"
    assert bmi_category(29.9) == "Overweight"
    assert bmi_category(30) == "Obesity"


def test_bmi_summary_from_profile_measurements():
    profile = SimpleNamespace(height_cm=170, weight_kg=70)

    summary = get_bmi_summary(profile)

    assert summary["value"] == 24.22
    assert summary["category"] == "Normal weight"
    assert summary["height_cm"] == 170
    assert summary["weight_kg"] == 70


def test_bmi_summary_handles_missing_or_invalid_measurements():
    assert get_bmi_summary(None) is None
    assert get_bmi_summary(SimpleNamespace(height_cm=None, weight_kg=70)) is None
    assert get_bmi_summary(SimpleNamespace(height_cm=170, weight_kg=None)) is None
    assert get_bmi_summary(SimpleNamespace(height_cm=0, weight_kg=70)) is None
    assert get_bmi_summary(SimpleNamespace(height_cm=170, weight_kg=-5)) is None
    assert get_bmi_summary(
        SimpleNamespace(height_cm="tall", weight_kg=70)
    ) is None


# ---------------------------------------------------------------------------
# Dashboard BMI display
# ---------------------------------------------------------------------------

PROFILE_FORM = {
    "age": "25",
    "sex": "female",
    "height_cm": "170",
    "weight_kg": "70",
    "activity_level": "moderate",
    "goal": "maintain",
}

PROFILE_JSON = {
    "age": 25,
    "sex": "female",
    "height_cm": 170,
    "weight_kg": 70,
    "activity_level": "moderate",
    "goal": "maintain",
}


def register_and_login(client, email, username="bmiuser"):
    client.post("/auth/register", data={
        "username": username,
        "email": email,
        "password": "password123",
    })
    client.post("/auth/login", data={
        "email": email,
        "password": "password123",
    })


def test_dashboard_shows_bmi_after_profile_setup():
    app = create_app()
    client = app.test_client()

    register_and_login(client, "bmi@example.com")
    client.post("/profile/", data=PROFILE_FORM)

    response = client.get("/reports/dashboard")

    assert response.status_code == 200
    assert b"24.2" in response.data                 # 70 kg / 1.70 m -> 24.22
    assert b"Normal weight" in response.data
    assert b"Estimate based on your current height" in response.data


def test_dashboard_bmi_updates_when_weight_changes():
    app = create_app()
    client = app.test_client()

    register_and_login(client, "bmi@example.com")
    client.post("/profile/", data=PROFILE_FORM)

    response = client.put("/profile/", json={
        **PROFILE_JSON,
        "weight_kg": 80,
    })

    assert response.status_code == 200
    assert response.get_json()["bmi"] == 27.68      # 80 kg / 1.70 m

    dashboard = client.get("/reports/dashboard")

    assert b"27.7" in dashboard.data
    assert b"Overweight" in dashboard.data
    assert b"Normal weight" not in dashboard.data


def test_dashboard_bmi_updates_when_height_changes():
    app = create_app()
    client = app.test_client()

    register_and_login(client, "bmi@example.com")
    client.post("/profile/", data=PROFILE_FORM)

    # Editing via the profile form must update the existing profile,
    # never create a second one.
    client.post("/profile/", data={**PROFILE_FORM, "height_cm": "180"})

    with app.app_context():
        assert Profile.query.count() == 1
        assert Profile.query.first().height_cm == 180

    dashboard = client.get("/reports/dashboard")

    assert b"21.6" in dashboard.data                # 70 kg / 1.80 m
    assert b"Normal weight" in dashboard.data


def test_dashboard_handles_invalid_measurements_safely():
    app = create_app()
    client = app.test_client()

    register_and_login(client, "bmi@example.com")
    client.post("/profile/", data=PROFILE_FORM)

    with app.app_context():
        profile = Profile.query.first()
        profile.height_cm = None
        db.session.commit()

    response = client.get("/reports/dashboard")

    assert response.status_code == 200
    assert b"Complete your profile to calculate your BMI" in response.data


def test_each_user_sees_only_their_own_bmi():
    app = create_app()

    client_a = app.test_client()
    register_and_login(client_a, "usera@example.com", "usera")
    client_a.post("/profile/", data=PROFILE_FORM)

    client_b = app.test_client()
    register_and_login(client_b, "userb@example.com", "userb")
    client_b.post("/profile/", data={
        **PROFILE_FORM,
        "height_cm": "160",
        "weight_kg": "95",
    })

    dashboard_a = client_a.get("/reports/dashboard")
    dashboard_b = client_b.get("/reports/dashboard")

    assert b"24.2" in dashboard_a.data              # 70 kg / 1.70 m
    assert b"Normal weight" in dashboard_a.data
    assert b"37.1" not in dashboard_a.data

    assert b"37.1" in dashboard_b.data              # 95 kg / 1.60 m
    assert b"Obesity" in dashboard_b.data
    assert b"24.2" not in dashboard_b.data
