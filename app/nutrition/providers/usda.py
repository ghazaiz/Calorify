import os

import requests
from dotenv import load_dotenv

load_dotenv()

USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


def search_food(food_name):
    api_key = os.getenv("USDA_API_KEY")

    response = requests.get(
        USDA_API_URL,
        params={
            "api_key": api_key,
            "query": food_name,
            "pageSize": 10
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("foods"):
        return None

    food = data["foods"][0]

    nutrients = {}

    for nutrient in food.get("foodNutrients", []):
        name = nutrient.get("nutrientName", "").lower()
        value = nutrient.get("value", 0)

        if "energy" in name:
            nutrients["calories"] = value

        elif "protein" in name:
            nutrients["protein"] = value

        elif "carbohydrate" in name:
            nutrients["carbohydrates"] = value

        elif "total lipid" in name:
            nutrients["fats"] = value

    return {
        "name": food.get("description", food_name),
        "serving_size": 100,
        "serving_unit": "g",
        "calories": nutrients.get("calories", 0),
        "protein": nutrients.get("protein", 0),
        "carbohydrates": nutrients.get("carbohydrates", 0),
        "fats": nutrients.get("fats", 0)
    }