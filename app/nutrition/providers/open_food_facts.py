import requests

from app.nutrition.matching import best_match, compatible_food
from app.nutrition.portions import CORE_NUTRIENTS, KJ_PER_KCAL, label_portions, number
from app.version import APP_VERSION


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"
HEADERS = {"User-Agent": f"Calorify/{APP_VERSION} (student calorie tracking project)"}
FIELDS = (
    "code,product_name,product_name_en,brands,product_quantity_unit,"
    "serving_size,serving_quantity,serving_quantity_unit,nutriments,no_nutrition_data"
)


def _nutrient(nutrients, key, maximum=100):
    value = number(nutrients.get(key))
    return value if value is not None and value <= maximum else None


def _record(product):
    name = product.get("product_name") or product.get("product_name_en")
    nutrients = product.get("nutriments")
    if not isinstance(name, str) or not name.strip() or not isinstance(nutrients, dict):
        return None
    if product.get("no_nutrition_data") in (True, "on", "1"):
        return None

    calories = number(nutrients.get("energy-kcal_100g"))
    if calories is None:
        kj = number(nutrients.get("energy-kj_100g"))
        if kj is None:
            kj = number(nutrients.get("energy_100g"))
        if kj is not None:
            calories = kj / KJ_PER_KCAL
    if calories is None or calories > 1000:
        return None

    # OFF uses the _100g suffix for both 100 g and 100 ml label data.
    serving_unit = str(product.get("serving_quantity_unit") or "").lower()
    package_unit = str(product.get("product_quantity_unit") or serving_unit).lower()
    basis_unit = "ml" if package_unit in {"ml", "cl", "dl", "l"} else "g"
    portions = label_portions(
        product.get("serving_quantity"), product.get("serving_size")
    ) if serving_unit == basis_unit else {}

    sodium = _nutrient(nutrients, "sodium_100g")
    code = str(product.get("code") or "")
    brand = product.get("brands")
    return {
        "name": name, "brand": brand if isinstance(brand, str) else None,
        "serving_size": 100, "serving_unit": basis_unit, "portions": portions,
        "calories": calories,
        "protein": _nutrient(nutrients, "proteins_100g"),
        "carbohydrates": _nutrient(nutrients, "carbohydrates_100g"),
        "fats": _nutrient(nutrients, "fat_100g"),
        "fiber": _nutrient(nutrients, "fiber_100g"),
        "sugars": _nutrient(nutrients, "sugars_100g"),
        "sodium_mg": sodium * 1000 if sodium is not None else None,
        "source_url": f"https://world.openfoodfacts.org/product/{code}" if code.isdigit() else None,
    }


def search_food(food_name):
    response = requests.get(
        OPEN_FOOD_FACTS_URL,
        params={
            "search_terms": food_name, "search_simple": 1, "action": "process",
            "json": 1, "page_size": 25, "fields": FIELDS,
        },
        headers=HEADERS,
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        return None

    candidates = []
    for product in data.get("products") or []:
        if isinstance(product, dict) and (record := _record(product)):
            if compatible_food(food_name, record["name"]) or (
                record["brand"] and compatible_food(food_name, f'{record["brand"]} {record["name"]}')
            ):
                candidates.append(record)

    def match_name(food):
        name = food["name"]
        return name if compatible_food(food_name, name) else f'{food["brand"]} {name}'

    complete = [food for food in candidates if all(food[key] is not None for key in CORE_NUTRIENTS)]
    return best_match(food_name, complete or candidates, get_name=match_name)
