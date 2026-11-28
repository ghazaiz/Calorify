## Calorify

Calorify is a Flask calorie-tracking application for logging meals, profiles,
nutrition searches, and reports.

### Run locally

From the `Calorify` directory:

```sh
python -m pip install -r requirements.txt
python main.py
```

For a Flask CLI or WSGI deployment, run `python -m flask --app main init-db`
before starting the app. This also upgrades existing databases for reports and profile settings. Set a persistent random `SECRET_KEY` shared by every production
worker. Optional nutrition credentials are listed in `.env.example`.

### Nutrition lookup

Set a free `USDA_API_KEY` in `.env` for USDA FoodData Central. Open Food Facts
uses public label data and needs no API key. Look up the specific preparation
or brand when possible. Amounts use the record's grams or milliliters, with
servings or pieces available when the source supplies a conversion.

Calorie Check also accepts sentences with weighed foods. Use the nutrition
label calculator for values from a package, or the homemade recipe calculator
for weighed ingredients, the finished batch weight, and your portion.
Database results are estimates and missing nutrients are marked on the result.

### Testing and delivery

Run `python -m pytest -q` from this directory. See [Testing](docs/testing.md)
for the test matrix. The project uses [Agile, incremental development](docs/project_plan.md)
and GitHub feature branches. The [operations runbook](docs/operations.md)
covers versioned distribution, staging, rolling deployment, monitoring, backups
and recovery. The [course evidence guide](docs/submission_evidence.md) maps
the assignment materials to the repository and the evidence to collect.

### Versioning

The application uses semantic versioning: `MAJOR.MINOR.PATCH`.

- `MAJOR`: breaking changes
- `MINOR`: backward-compatible features
- `PATCH`: bug fixes and small corrections

The current version is defined centrally in `app/version.py` and displayed in
the application sidebar and profile settings. Run `python -m flask --app main app-version` to print
it from the command line. See [CHANGELOG.md](CHANGELOG.md) for release history.
