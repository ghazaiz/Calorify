from app import create_app
from app.core.extensions import db
from app.authentication.service import register_user
from app.meals.service import add_meal, get_user_meals


def test_add_and_get_meal():
    app = create_app()

    with app.app_context():
        db.create_all()

        user = register_user(
            "mealuser",
            "meal@example.com",
            "password123"
        )

        meal = add_meal(
            user.user_id,
            "Chicken Biryani",
            "lunch",
            300,
            "g",
            515,
            44.5,
            39,
            20
        )

        meals = get_user_meals(user.user_id)

        assert meal is not None
        assert len(meals) == 1
        assert meals[0].food_name == "Chicken Biryani"

def test_meal_routes_reject_nonfinite_nutrients_and_invalid_dates():
    app = create_app()
    client = app.test_client()
    client.post("/auth/register", data={
        "username": "mealuser", "email": "meal@example.com", "password": "password123"
    })
    client.post("/auth/login", data={
        "email": "meal@example.com", "password": "password123"
    })
    payload = {
        "food_name": "Rice", "meal_type": "lunch", "quantity": 100,
        "serving_unit": "g", "calories": 130, "protein": 3,
        "carbohydrates": 28, "fats": 0.3,
    }

    for change in ({"protein": "nan"}, {"date": 123}, {"meal_type": ["lunch"]}):
        assert client.post("/meals/", json={**payload, **change}).status_code == 400

    response = client.post("/meals/", json=payload)
    assert response.status_code == 201
    meal_id = response.get_json()["meal"]["meal_id"]
    assert client.put(f"/meals/{meal_id}", json={**payload, "fats": "inf"}).status_code == 400
    saved = client.get("/meals/", headers={"Accept": "application/json"}).get_json()
    assert saved["meals"][0]["fats"] == 0.3


def test_lookup_logged_meal_updates_dashboard_and_week_after_edit_and_delete(monkeypatch):
    app = create_app()
    client = app.test_client()
    credentials = {"email": "flow@example.com", "password": "password123"}
    assert client.get("/reports/dashboard").status_code == 302
    assert client.get("/meals/", headers={"Accept": "application/json"}).status_code == 401
    registration = client.post("/auth/register", data={"username": "flow", **credentials})
    assert b"Account created" in registration.data
    assert client.post("/auth/login", data=credentials).status_code == 302

    from app.nutrition import service
    monkeypatch.setattr(service, "search_usda_food", lambda query: {
        "name": "Rice, cooked", "serving_size": 100, "serving_unit": "g",
        "calories": 130, "protein": 3, "carbohydrates": 28, "fats": 0.3,
        "portions": {"serving": 150},
    })
    headers = {"Accept": "application/json"}
    result = client.get("/nutrition/search?food=rice&quantity=2&unit=serving", headers=headers)
    assert result.status_code == 200
    food = result.get_json()["food"]
    payload = {
        "food_name": food["name"], "meal_type": "lunch",
        "quantity": food["quantity"], "serving_unit": food["quantity_unit"],
        **{key: food[key] for key in ("calories", "protein", "carbohydrates", "fats")},
    }
    created = client.post("/meals/", json=payload)
    assert created.status_code == 201
    meal_id = created.get_json()["meal"]["meal_id"]
    assert client.get("/reports/daily").get_json()["calories"] == 390
    assert b"Rice, cooked" in client.get("/reports/dashboard").data

    updated = {
        **payload, "quantity": 1,
        **{key: payload[key] / 2 for key in ("calories", "protein", "carbohydrates", "fats")},
    }
    assert client.put(f"/meals/{meal_id}", json=updated).status_code == 200
    assert client.get("/reports/daily").get_json()["calories"] == 195
    assert client.get("/reports/weekly", headers=headers).get_json()["report"][-1]["calories"] == 195
    assert client.get("/reports/weekly").status_code == 200
    assert client.delete(f"/meals/{meal_id}").status_code == 200
    assert client.get("/reports/daily").get_json()["meal_count"] == 0
    assert client.get("/reports/weekly", headers=headers).get_json()["report"][-1]["calories"] == 0
