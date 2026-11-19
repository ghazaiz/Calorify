import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from app.nutrition.matching import normalize_query
from app.nutrition.providers.gemini import get_nutrition_from_gemini
from app.nutrition.providers.usda import search_food as search_usda_food
from app.nutrition.providers.open_food_facts import search_food as search_off_food


logger = logging.getLogger(__name__)


# Hard cap on how long we wait for Gemini before falling back to the
# other providers. The SDK can hang for minutes when the model is
# overloaded, which would freeze the whole search request.
GEMINI_TIMEOUT_SECONDS = 15

_gemini_executor = ThreadPoolExecutor(max_workers=2)


def search_food(
    food_name,
    quantity_grams=None,
    meat_weight_grams=None
):
    food_name = normalize_query(food_name)

    if not food_name:
        return None

    # 1. Gemini - understands natural language and mixed dishes.
    try:
        future = _gemini_executor.submit(
            get_nutrition_from_gemini,
            food_name,
            quantity_grams,
            meat_weight_grams
        )

        nutrition = future.result(timeout=GEMINI_TIMEOUT_SECONDS)

        if nutrition:
            return {
                "source": "gemini",
                "food": nutrition
            }

    except FutureTimeoutError:
        logger.warning(
            "Gemini timed out after %ss for %r; "
            "falling back to USDA / Open Food Facts",
            GEMINI_TIMEOUT_SECONDS,
            food_name
        )
    except Exception as error:
        logger.warning(
            "Gemini provider failed for %r: %s", food_name, error
        )

    # 2. USDA - generic reference foods. Returns None instead of an
    # irrelevant food, so the search can continue to Open Food Facts.
    try:
        usda_food = search_usda_food(food_name)

        if usda_food:
            return {
                "source": "usda",
                "food": usda_food
            }

    except Exception as error:
        logger.warning(
            "USDA provider failed for %r: %s", food_name, error
        )

    # 3. Open Food Facts - packaged products, as a last resort.
    try:
        off_food = search_off_food(food_name)

        if off_food:
            return {
                "source": "open_food_facts",
                "food": off_food
            }

    except Exception as error:
        logger.warning(
            "Open Food Facts provider failed for %r: %s", food_name, error
        )

    return None
