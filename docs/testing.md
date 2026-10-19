# Calorify — Testing

## 1. Testing Approach

Calorify uses automated tests (Pytest) for service-layer logic and provider response schemas, plus manual testing of the web interface. Testing happens throughout development rather than only at the end:

**Develop → Test → Fix → Retest → Refactor**

## 2. Test Environment and Isolation

* Framework: **Pytest 9.1.1** on Python 3.11.
* The suite lives in `tests/`, one file per module.
* `tests/conftest.py` repoints the database URI at a throwaway file in the system temp directory (`calorify_test.db`) **before** any test runs, and an autouse fixture drops and recreates all tables before each test. The real `calorify.db` is never touched by tests.
* Live external-API tests are **opt-in** (see §5), so the default run needs no internet access and no API keys.

## 3. Running the Tests

From the `Calorify/` project folder, with the virtual environment active:

```powershell
# Install dependencies (once)
pip install -r requirements.txt

# Run the whole suite
python -m pytest

# Verbose output
python -m pytest -v

# One file
python -m pytest tests/test_profile.py

# One test
python -m pytest tests/test_nutrition.py::test_mixed_dish_components_do_not_double_count
```

To include the live provider-integration tests (requires internet access plus `GEMINI_API_KEY` / `USDA_API_KEY` in `.env`):

```powershell
$env:RUN_INTEGRATION_TESTS = "1"; python -m pytest tests/test_nutrition.py
```

## 4. Current Automated Tests

| File | Test | Type | What it verifies |
| --- | --- | --- | --- |
| `test_profile.py` | `test_calculate_bmi` | Unit | BMI formula (170 cm / 70 kg → 24.22) |
| `test_profile.py` | `test_calculate_macro_targets` | Unit | 21/54/25% macro split of a 2400 kcal target (126 g protein, 324 g carbs, 66.7 g fat) |
| `test_profile.py` | `test_calculate_daily_calorie_target` | Unit | Calorie target stays above the 1200 kcal floor for a sample profile |
| `test_meals.py` | `test_add_and_get_meal` | Service/DB integration | Registering a user, adding a meal and reading it back through the service layer |
| `test_reports.py` | `test_daily_report_empty` | Service/DB integration | Daily report returns zero totals and zero meal count for a user with no meals |
| `test_reports.py` | `test_weekly_report_returns_seven_days` | Service/DB integration | Weekly report always covers exactly 7 days |
| `test_nutrition.py` | `test_mixed_dish_schema_accepts_components` | Unit (schema) | The Pydantic `NutritionResult` schema accepts a mixed-dish payload with components, estimate flag and meat weight |
| `test_nutrition.py` | `test_mixed_dish_components_do_not_double_count` | Unit (schema) | On a sample chicken-biryani payload, component grams and calories sum to the whole-dish totals and the meat weight is less than the total (no double counting) |
| `test_nutrition.py` | `test_simple_food_without_components_is_valid` | Unit (schema) | A simple food (raw banana) validates without a component list |
| `test_nutrition.py` | `test_search_food` | External API integration (opt-in) | The live fallback chain returns a result with `source` and `food` keys for "apple" |
| `test_nutrition.py` | `test_search_mixed_dish` | External API integration (opt-in) | A live mixed-dish search ("chicken biryani", 300 g total, 150 g meat) returns positive calories |

`tests/test_authentication.py` currently contains only a database fixture and **no test functions** — the Authentication module has no automated coverage yet. This is a known gap (see §7).

## 5. Latest Results

Default run on 2026-10-09 (Windows, Python 3.11.15, Pytest 9.1.1):

```text
11 collected: 9 passed, 2 skipped
```

The two skipped tests are the live provider-integration tests, which are gated behind `RUN_INTEGRATION_TESTS=1` because they need internet access, a valid `GEMINI_API_KEY` (primary provider) and `USDA_API_KEY`, and their results depend on live external services.

Code coverage is not currently measured (no coverage plugin is installed); the earlier 80% coverage target remains an aspiration, not a verified figure.

## 6. Manual Demonstration Steps

The web flows are verified manually in a browser (`python main.py`, then http://127.0.0.1:5000):

1. **Guest search** — open `/nutrition/guest`, search "chicken biryani", confirm the result card, the "~ Estimated" chip and the "What's inside" component list; confirm the session history fills and no login was needed.
2. **Register and log in** — create an account at `/auth/register` (duplicate email and short passwords are rejected), then log in.
3. **Profile** — fill in body details, pick "Lose weight" and a weekly pace; confirm calorie and macro goals appear and the dashboard opens.
4. **Calorie Check (member)** — search a mixed dish with total and meat weights; confirm the "How it fits your day" card and add the result to today.
5. **Meals** — log, edit, delete and re-log meals; confirm category filters and search.
6. **Reports** — check today's totals on the dashboard and the weekly report's bar chart, macro split and insights.
7. **Account** — change password, export data as JSON, and (with a disposable account) delete the account.

## 7. Known Testing Limitations

* **No authentication tests** — `test_authentication.py` is an empty shell; registration, login, duplicate-email and invalid-login cases are untested.
* **No HTTP route tests** — the suite tests services directly; no Flask `test_client` tests cover status codes, content negotiation, `@login_required` behaviour or ownership (404 for another user's meal).
* **No mocked provider tests** — the fallback chain (Gemini → USDA → Open Food Facts) is only exercised by the opt-in live tests; there are no tests with mocked HTTP responses for provider failure, timeout or "food not found". The schema tests validate a *sample* payload, not live model output.
* **Gemini output is non-deterministic** — the no-double-counting property is enforced by prompt instructions and checked on a fixed sample payload; it is not numerically re-verified on real responses at runtime.
* The frontend JavaScript (modals, water tracker, theme, filters) is only tested manually.

## 8. Nutrition API Demonstration

The search endpoint serves JSON when the client prefers it via the `Accept` header (browsers get HTML from the same URL).

**Request** (mixed Desi dish with explicit weights — the meat weight is part of the total, not additional):

```bash
curl "http://127.0.0.1:5000/nutrition/search?food=chicken+biryani&quantity=300&meat_weight=150" \
     -H "Accept: application/json"
```

**Response** (illustrative example of the real schema; Gemini values vary between runs because they are estimates):

```json
{
  "source": "gemini",
  "food": {
    "name": "Chicken Biryani",
    "quantity_grams": 300.0,
    "meat_weight_grams": 150.0,
    "calories": 596.0,
    "protein": 44.3,
    "carbohydrates": 41.6,
    "fats": 27.1,
    "estimate": true,
    "components": [
      { "name": "Chicken (cooked)", "grams": 150.0, "calories": 285.0,
        "protein": 40.0, "carbohydrates": 0.0, "fats": 13.5 },
      { "name": "Cooked basmati rice", "grams": 130.0, "calories": 169.0,
        "protein": 3.5, "carbohydrates": 41.0, "fats": 0.4 },
      { "name": "Oil, fried onion & spices", "grams": 20.0, "calories": 142.0,
        "protein": 0.8, "carbohydrates": 0.6, "fats": 13.2 }
    ]
  }
}
```

When Gemini is unavailable, `source` is `"usda"` or `"open_food_facts"` and `food` is a flat object with `serving_size: 100`, `serving_unit: "g"` and per-100 g `calories` / `protein` / `carbohydrates` / `fats` — no components and no use of the weight parameters. If no provider finds the food, the endpoint returns `404` with `{"message": "Food not found"}`.

**Security note:** demonstrations must use keys from the local `.env` file; API keys, passwords and other secrets are never included in documentation, commits or screenshots.
