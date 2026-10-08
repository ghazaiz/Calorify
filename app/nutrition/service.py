from app.nutrition.providers.gemini import get_nutrition_from_gemini
from app.nutrition.providers.usda import search_food as search_usda_food
from app.nutrition.providers.open_food_facts import search_food as search_off_food


def search_food(
    food_name,
    quantity_grams=None,
    meat_weight_grams=None
):
    # 1. Gemini
    try:
        nutrition = get_nutrition_from_gemini(
            food_name,
            quantity_grams,
            meat_weight_grams
        )

        if nutrition:
            return {
                "source": "gemini",
                "food": nutrition
            }

    except Exception as error:
        print("GEMINI ERROR:", error)

    # 2. USDA
    try:
        usda_food = search_usda_food(food_name)

        if usda_food:
            return {
                "source": "usda",
                "food": usda_food
            }

    except Exception:
        pass

    # 3. Open Food Facts
    try:
        off_food = search_off_food(food_name)

        if off_food:
            return {
                "source": "open_food_facts",
                "food": off_food
            }

    except Exception:
        pass

    return None