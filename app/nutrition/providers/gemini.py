import os

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

from app.core.exceptions import ProviderNotConfiguredError


load_dotenv()


class NutritionComponent(BaseModel):
    """One part of a mixed dish, e.g. the rice or the chicken."""

    name: str
    grams: float
    calories: float
    protein: float
    carbohydrates: float
    fats: float


class NutritionResult(BaseModel):
    name: str
    quantity_grams: float
    meat_weight_grams: float | None
    calories: float
    protein: float
    carbohydrates: float
    fats: float
    estimate: bool
    components: list[NutritionComponent] | None = None


PROMPT_TEMPLATE = """
You are the nutrition engine for Calorify, a calorie-tracking app used
heavily for Desi / South Asian food. Estimate nutrition for one food
entry using the component method described below.

Food entry: {food_name}
Total dish amount: {quantity_text}
{meat_text}

## Step 1 - read the quantities

- The user may write quantities inside the food text itself, e.g.
  "300g chicken biryani with 150g chicken" or
  "1 plate biryani, approximately 350g, with 120g chicken" or
  "250g daal chawal, half rice and half daal".
  Extract them when present.
- Explicit amounts given above ("Total dish amount", meat weight)
  OVERRIDE anything written in the food text.
- If no amount is given anywhere, assume one normal single serving of
  the dish and report the grams you assumed in quantity_grams.
- If the dish contains meat but no meat weight is given, assume a
  typical meat share for that dish.

## Step 2 - decompose mixed dishes into components

For a mixed dish (biryani, pulao, karahi, curry/salan, daal chawal,
haleem, a sandwich, a burger, ...):

1. Split the TOTAL amount into its real components, for example:
   - biryani: meat + cooked rice + oil/ghee, fried onion, spices
   - karahi:  meat + tomato-oil gravy
   - daal chawal: cooked daal + cooked rice + tadka oil
2. CRITICAL - no double counting: the meat weight is ALREADY INCLUDED
   in the total. Non-meat portion = total grams - meat grams. The
   component grams must add up to the total grams (oil absorbed into
   the dish may be listed with small or zero grams but real calories).
3. Compute calories, protein, carbohydrates and fats for EACH
   component from its own grams, using standard cooked-food values.
4. The top-level numbers MUST be the sum over the components - the
   complete dish, never just the meat and never just the rice.
5. Return the component list in "components" (2-5 entries, biggest
   first). For a simple single food (banana, boiled egg, plain rice),
   omit components or return a single entry.

## Step 3 - mark accuracy honestly

Recipes vary (oil, rice-to-meat ratio, cooking method), so set
"estimate": true for any mixed or cooked dish. Only a plain single
food with well-known values (e.g. a raw banana) may use false.

Return: food name, total quantity_grams, meat_weight_grams (null when
the dish has no meat), total calories / protein / carbohydrates / fats
for the WHOLE dish, estimate flag, and the components breakdown.
"""


def get_nutrition_from_gemini(
    food_name,
    quantity_grams=None,
    meat_weight_grams=None
):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ProviderNotConfiguredError("GEMINI_API_KEY is not configured")

    # Fail fast: 15s cap and no retry backoff, so an overloaded Gemini
    # falls through to USDA / Open Food Facts instead of hanging the
    # whole search request for minutes.
    client = genai.Client(
        api_key=api_key,
        http_options={
            "timeout": 15_000,
            "retry_options": {"attempts": 1}
        }
    )

    quantity_text = (
        f"{quantity_grams} grams"
        if quantity_grams is not None
        else "not specified"
    )

    meat_text = (
        f"Meat weight: {meat_weight_grams} grams (already included in the total)."
        if meat_weight_grams is not None
        else ""
    )

    prompt = PROMPT_TEMPLATE.format(
        food_name=food_name,
        quantity_text=quantity_text,
        meat_text=meat_text
    )

    response = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": NutritionResult.model_json_schema()
        }
    )

    result = NutritionResult.model_validate_json(
        response.output_text
    )

    return result.model_dump()
