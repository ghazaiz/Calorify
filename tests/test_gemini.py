import os

import pytest
from dotenv import load_dotenv
from google import genai

load_dotenv()

@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Live Gemini checks require RUN_INTEGRATION_TESTS=1"
)
def test_gemini_connection():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        pytest.skip("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    response = client.interactions.create(
        model="gemini-3.8-flash",
        input="Say exactly: Gemini is connected to Calorify!"
    )

    assert response.output_text