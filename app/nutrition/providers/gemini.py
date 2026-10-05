import os

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel


load_dotenv()


class NutritionResult(BaseModel):
    name: str
    quantity_grams: float
    meat_weight_grams: float | None
    calories: float
    protein: float
    carbohydrates: float
    fats: float
    estimate: bool


def get_nutrition_from_gemini(
    food_name,
    quantity_grams=None,
    meat_weight_grams=None
):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    quantity_text = (
        f"{quantity_grams} grams"
        if quantity_grams is not None
        else "a normal serving"
    )

    meat_text = ""

    if meat_weight_grams is not None:
        meat_text = (
            f"The dish contains {meat_weight_grams} grams of meat."
        )

    prompt = f"""
You are the nutrition engine for Calorify.

Estimate nutrition for this food.

Food: {food_name}
Total dish amount: {quantity_text}
{meat_text}

IMPORTANT:
- The quantity is the TOTAL amount of the dish.
- If a meat weight is provided, that meat is ALREADY INCLUDED
  inside the total dish amount.
- Do NOT add the meat on top of the total dish amount.
- For biryani, curry, karahi, pulao and similar mixed dishes,
  estimate nutrition based on the total dish amount and
  the specified meat amount.
- If no meat weight is provided, estimate a reasonable meat amount
  when the food normally contains meat.
- Return estimated values because recipes vary.

Return:
- food name
- total quantity in grams
- meat weight in grams, if applicable
- calories
- protein in grams
- carbohydrates in grams
- fats in grams
"""

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