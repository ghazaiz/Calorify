import requests

from app.nutrition.matching import best_match


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"

HEADERS = {
    "User-Agent": "Calorify/1.0 (student calorie tracking project)"
}


def _product_name(product):
    return (
        product.get("product_name")
        or product.get("product_name_en")
        or ""
    )


def search_food(food_name):
    try:
        response = requests.get(
            OPEN_FOOD_FACTS_URL,
            params={
                "search_terms": food_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 20
            },
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException:
        return None

    # Only consider products that carry both a name and calorie data,
    # then rank them by name relevance instead of trusting the first
    # hit. A calorie tracker must not return a 0-kcal placeholder.
    candidates = [
        product for product in data.get("products", [])
        if _product_name(product)
        and product.get("nutriments", {}).get("energy-kcal_100g") is not None
    ]

    product = best_match(
        food_name,
        candidates,
        get_name=_product_name
    )

    if product is None:
        return None

    nutrients = product.get("nutriments", {})

    return {
        "name": _product_name(product),
        "serving_size": 100,
        "serving_unit": "g",
        "calories": nutrients.get("energy-kcal_100g", 0),
        "protein": nutrients.get("proteins_100g", 0),
        "carbohydrates": nutrients.get("carbohydrates_100g", 0),
        "fats": nutrients.get("fat_100g", 0)
    }
