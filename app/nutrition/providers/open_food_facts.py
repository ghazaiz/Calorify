import requests


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"

HEADERS = {
    "User-Agent": "Calorify/1.0 (student calorie tracking project)"
}


def search_food(food_name):
    try:
        response = requests.get(
            OPEN_FOOD_FACTS_URL,
            params={
                "search_terms": food_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 10
            },
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException:
        return None

    products = data.get("products", [])

    if not products:
        return None

    product = products[0]
    nutrients = product.get("nutriments", {})

    return {
        "name": product.get("product_name", food_name),
        "serving_size": 100,
        "serving_unit": "g",
        "calories": nutrients.get("energy-kcal_100g", 0),
        "protein": nutrients.get("proteins_100g", 0),
        "carbohydrates": nutrients.get("carbohydrates_100g", 0),
        "fats": nutrients.get("fat_100g", 0)
    }