import re
from math import floor, isfinite


CORE_NUTRIENTS = ("calories", "protein", "carbohydrates", "fats")
OPTIONAL_NUTRIENTS = ("fiber", "sugars", "sodium_mg")
NUTRIENTS = CORE_NUTRIENTS + OPTIONAL_NUTRIENTS
MIN_QUANTITY = 0.01
MAX_QUANTITY = 100_000
KJ_PER_KCAL = 4.184


def number(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return value if isfinite(value) and value >= 0 else None


def label_portions(size, label):
    size = number(size)
    if not size:
        return {}
    portions = {"serving": size}
    pieces = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s+pieces?\b", str(label or ""), re.I)
    if pieces and float(pieces[1]) >= 1:
        portions["piece"] = size / float(pieces[1])
    return portions


def portion_options(food):
    basis_unit = food["serving_unit"]
    units = {basis_unit: 1}
    units.update(food.get("portions", {}))
    return units


def scale_food(food, amount, unit):
    size = portion_options(food).get(unit)
    if size is None:
        return None
    weight = amount * size
    if not 0 < weight <= MAX_QUANTITY:
        return None
    factor = weight / food["serving_size"]
    result = {
        **food,
        "quantity": amount,
        "quantity_unit": unit,
        "basis_amount": weight,
        "quantity_grams": weight if food["serving_unit"] == "g" else None,
    }
    for nutrient in NUTRIENTS:
        value = number(food.get(nutrient))
        result[nutrient] = floor(value * factor * 100 + 0.5) / 100 if value is not None else None
    result["complete"] = all(result[key] is not None for key in CORE_NUTRIENTS)
    return result
