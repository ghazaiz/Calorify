import re

from app.nutrition.matching import normalize_query
from app.nutrition.portions import MAX_QUANTITY, MIN_QUANTITY, number


AMOUNT = re.compile(
    r"(?<![\w.])(?P<amount>[+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*"
    r"(?P<unit>kilograms?|kg|grams?|g|milliliters?|ml|servings?|pieces?)\b",
    re.I,
)
LEAD_IN = re.compile(
    r"^(?:please\s+|(?:how many calories(?: are there)?(?: in| for)?|"
    r"i (?:just )?(?:ate|had|drank|have)|calories (?:in|for)|"
    r"check(?: the)? calories (?:in|for))\s*[:?]?\s*)+",
    re.I,
)
BIRYANI = re.compile(r"\b(?:biryani|biriyani|briyani)\b", re.I)
SEPARATOR = re.compile(r",\s*(?:and\s+)?|\s+(?:and|with|plus|including)\s+|\s*\+\s*", re.I)
UNITS = {**dict.fromkeys("kg", "g"), "m": "ml", "s": "serving", "p": "piece"}
FOOD_ALIASES = {
    "daal": "cooked lentils", "dal": "cooked lentils", "chawal": "cooked rice",
    "anda": "egg", "dahi": "plain yogurt", "aloo": "potato",
    "chana": "cooked chickpeas", "bhindi": "okra", "roti": "chapati",
}
CHICKEN_CUTS = {"breast": "Cooked chicken breast", "thigh": "Cooked chicken thigh"}
CHICKEN_NAMES = {
    "chicken": "breast",
    "chicken breast": "breast", "cooked chicken breast": "breast",
    "chicken thigh": "thigh", "cooked chicken thigh": "thigh",
}


def valid_amount(amount):
    return amount is not None and MIN_QUANTITY <= amount <= MAX_QUANTITY


def parse_meal(text, *, recipe=False):
    text = LEAD_IN.sub("", normalize_query(text)).strip(" .!?")
    text = re.sub(r"\s+(?:please|for (?:breakfast|lunch|dinner))$", "", text, flags=re.I)
    amounts = list(AMOUNT.finditer(text))
    if not amounts:
        return [(text, None, None)]

    parts = [text]
    if len(amounts) > 1:
        parts = SEPARATOR.split(text)
        if len(parts) != len(amounts) or any(len(list(AMOUNT.finditer(part))) != 1 for part in parts):
            parts = re.split(rf"{SEPARATOR.pattern}(?={AMOUNT.pattern})", text, flags=re.I)
            if len(parts) != len(amounts) or any(not AMOUNT.search(part) for part in parts):
                raise ValueError("Give each food an amount, for example 150 g rice and 100 g chicken.")
    items = []
    for part in parts:
        match = AMOUNT.search(part)
        amount = number(match["amount"])
        unit = match["unit"].lower()
        if unit.startswith("k"):
            amount = amount * 1000 if amount is not None else None
        unit = UNITS[unit[0]]
        before, after = part[:match.start()].strip(), part[match.end():].strip()
        before = re.sub(
            r"(?:\b(?:weigh(?:ing|s)|about|around|approximately)\s*)*[:(]?\s*$", "", before, flags=re.I,
        ).strip()
        if before.lower() in {"a", "an"}:
            before = ""
        after = re.sub(r"^of\s+", "", after, flags=re.I).strip(" )")
        name = normalize_query(f"{before} {after}").strip(" ,.:")
        if not name or not valid_amount(amount):
            raise ValueError("Enter a food name and a positive amount, for example 150 g cooked rice.")
        items.append((name, amount, unit))

    if not recipe and len(items) == 2 and BIRYANI.search(items[0][0]) and items[1][0].lower() in CHICKEN_NAMES:
        dish, chicken = items
        if dish[2] == chicken[2] == "g":
            includes_chicken = re.search(r"\bincluding\b", text, re.I) or (
                "chicken" in dish[0].lower().split() and re.search(r"\bwith\b", text, re.I)
            )
            rice = dish[1] - chicken[1] if includes_chicken else dish[1]
            cut = CHICKEN_NAMES[chicken[0].lower()]
            return biryani_items(rice, chicken[1], cut)
    if re.search(r"\bincluding\b", text, re.I) and len(items) > 1:
        raise ValueError("Enter separate amounts for each part of the meal so ingredients are counted once.")
    return [
        (CHICKEN_CUTS[CHICKEN_NAMES[name.lower()]], amount, unit)
        if not recipe and name.lower() in CHICKEN_NAMES and name.lower() != "chicken" else (name, amount, unit)
        for name, amount, unit in items
    ]


def biryani_items(rice, chicken, cut="breast"):
    if not valid_amount(rice) or not valid_amount(chicken):
        raise ValueError("Enter positive gram amounts for the biryani rice and chicken.")
    if cut not in CHICKEN_CUTS:
        raise ValueError("Choose chicken breast or thigh.")
    return [("Biryani rice", rice, "g"), (CHICKEN_CUTS[cut], chicken, "g")]
