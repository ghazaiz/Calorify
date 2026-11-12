import os

import requests
from dotenv import load_dotenv

from app.core.exceptions import ProviderNotConfiguredError
from app.nutrition.matching import best_match

load_dotenv()

USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Generic reference entries describe plain foods ("Eggs, Grade A,
# Large, egg whole") while Branded entries are packaged products. On a
# near-tie prefer the generic food, without excluding branded results.
DATA_TYPE_BONUS = {
    "Foundation": 0.10,
    "SR Legacy": 0.08,
    "Survey (FNDDS)": 0.04,
}

KCAL_PER_KJ = 1 / 4.184


def search_food(food_name):
    api_key = os.getenv("USDA_API_KEY")

    if not api_key:
        raise ProviderNotConfiguredError("USDA_API_KEY is not configured")

    response = requests.get(
        USDA_API_URL,
        params={
            "api_key": api_key,
            "query": food_name,
            "pageSize": 25
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    # Rank every returned food by how well its name matches the query,
    # instead of trusting USDA's first result ("eggs" must not come
    # back as "Egg custard"). Returns None when nothing is relevant so
    # the search can fall through to the next provider.
    food = best_match(
        food_name,
        data.get("foods") or [],
        get_name=lambda candidate: candidate.get("description", ""),
        get_bonus=lambda candidate: DATA_TYPE_BONUS.get(
            candidate.get("dataType"), 0.0
        )
    )

    if food is None:
        return None

    nutrients = {}
    energy_kcal = None
    energy_kj = None

    for nutrient in food.get("foodNutrients", []):
        name = (nutrient.get("nutrientName") or "").lower()
        unit = (nutrient.get("unitName") or "").lower()
        value = nutrient.get("value", 0)

        if "energy" in name:
            # Foods often list energy twice (kcal and kJ); keep them
            # apart so a kJ value is never reported as calories.
            if unit == "kcal" and energy_kcal is None:
                energy_kcal = value
            elif unit == "kj" and energy_kj is None:
                energy_kj = value

        elif "protein" in name and "protein" not in nutrients:
            nutrients["protein"] = value

        elif "carbohydrate" in name and "carbohydrates" not in nutrients:
            nutrients["carbohydrates"] = value

        elif "total lipid" in name and "fats" not in nutrients:
            nutrients["fats"] = value

    if energy_kcal is not None:
        calories = energy_kcal
    elif energy_kj is not None:
        calories = round(energy_kj * KCAL_PER_KJ, 1)
    else:
        calories = 0

    return {
        "name": food.get("description", food_name),
        "serving_size": 100,
        "serving_unit": "g",
        "calories": calories,
        "protein": nutrients.get("protein", 0),
        "carbohydrates": nutrients.get("carbohydrates", 0),
        "fats": nutrients.get("fats", 0)
    }
