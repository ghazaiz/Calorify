# Calorify testing

Run from the `Calorify` directory with the virtual environment active.

```powershell
python -m pytest
node --check app/static/js/script.js
```

Pytest gives each test its own temporary SQLite database. The main suite
uses provider response fixtures and tests registration, login, profiles,
food matching, nutrient parsing, portions, fallback failures, meal logging,
and daily and weekly totals after a meal is added, modified, or deleted.

## Test levels and release evidence

| Level | Calorify example |
| --- | --- |
| Unit | Nutrition scaling, provider matching, and profile calculations |
| Database | User isolation, meal persistence, and account deletion in temporary SQLite files |
| Route | Login redirects, invalid meal quantities, and readiness on an unavailable schema |
| Integration | The workflow runs the extracted release over HTTP and verifies nutrition lookup, save, retrieval and reports |
| Recovery | Snapshot, restore and integrity checks on the staging SQLite file |
| Manual browser | Check navigation, responsive forms, light and dark mode, and use **Log meal** from a nutrition search result |

Run the HTTP exercise against an isolated test instance with
`python deployment/smoke.py http://127.0.0.1:5000`. It creates a temporary account
and deletes it at the end. Use `--health-only` for a read-only readiness check.
See [operations](operations.md) for the release gates and the [evidence guide](submission_evidence.md)
for artifacts to collect.

## Live provider tests

Open Food Facts needs internet access. USDA FoodData Central also needs
a free `USDA_API_KEY` in the environment or `.env`.

```powershell
$env:RUN_INTEGRATION_TESTS = "1"
python -m pytest tests/test_nutrition.py -k live
```

## Browser checks

1. Start the app with `python main.py` and open `http://127.0.0.1:5000`.
2. Search for banana as a guest. Change the amount to 150 g and check the source and updated nutrients.
3. Register, sign in, and save a profile. Confirm the dashboard shows the saved targets.
4. Find a food with a complete result and log it. Confirm the dashboard and weekly report include it.
5. Edit the logged amount and confirm the same-unit nutrition changes proportionally. Delete the meal and confirm the totals decrease.
6. Check the navigation, forms, and result card in desktop and phone widths.

For API clients, request `GET /nutrition/search?food=banana&quantity=150&unit=g`
with `Accept: application/json`. The `reference` object contains the provider
basis and `food` contains the scaled values. Nutrients missing from the provider
are JSON `null`. A successful result can be incomplete. Check `food.complete`
before offering to log the lookup.

| Status | Meaning |
| --- | --- |
| 400 | The food name, amount, or unit is invalid |
| 404 | No compatible database record was found |
| 422 | The selected record cannot convert the requested portion |
| 503 | The nutrition databases are unavailable |
