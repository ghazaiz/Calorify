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