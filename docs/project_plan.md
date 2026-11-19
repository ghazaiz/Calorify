# Calorify — Project Plan

## 1. Development Methodology

Calorify is developed using the **Agile methodology**: short development cycles, regular progress reviews, testing of completed features, and continuous refactoring.

**Plan → Design → Develop → Test → Review → Refactor**

## 2. Team Structure

The project team consists of five members with four responsibility areas.

| Role | Members | Main responsibilities |
| --- | ---: | --- |
| Developer | 2 | Writes, maintains and integrates application code |
| UI/UX Designer | 1 | Plans the user interface and user experience |
| QA / Tester | 1 | Tests features, identifies bugs and verifies fixes |
| Technical Writer | 1 | Prepares and maintains project documentation |

All team members participate in project discussions, sprint reviews and coordination.

## 3. Original One-Week Plan and Current Status

The project was planned as a one-week build. The table below maps each planned work area to its current status, based on inspection of the codebase (see `docs/requirements.md` for per-requirement detail).

| Planned area | Status |
| --- | --- |
| Flask environment, SQLite + SQLAlchemy setup, database models, app factory | **Done** |
| Registration, login/logout, password hashing | **Done** |
| Profile with calorie-goal calculation (Mifflin–St Jeor, activity levels, loss pace, macro targets, BMI) | **Done** — the BMI warning is computed but only surfaced through the JSON profile API, not the web form flow |
| Nutrition provider integration | **Done, with a changed design** — Google Gemini was added as the primary provider; USDA FoodData Central and Open Food Facts are now the fallbacks (the original plan had USDA as primary) |
| Mixed Desi-dish estimates (biryani, karahi, daal chawal, …) with total/meat weights and component breakdown | **Done via Gemini only** — fallback providers return flat per-100 g values without components |
| Guest nutrition search (no account required) | **Done** (added after the original plan) |
| Meal logging, categories, editing, deleting | **Done** |
| Dashboard, daily summary, weekly report, charts | **Done** — charts are CSS-rendered (bar chart, donut, progress rings) |
| UI integration, navigation, error messages, responsive styling | **Done** — includes a light/dark theme and a browser-local water tracker beyond the original scope |
| Testing and refactoring | **Partially done** — service-layer and schema tests pass (9 passed, 2 skipped live-API tests); authentication and HTTP-route tests are still missing |
| Finalisation (docs, demo, final review) | **In progress** — documentation synchronised; remaining tasks listed in §6 |

## 4. Development Rules

* The application stays divided into exactly five main functional modules:
  1. Authentication
  2. Profile
  3. Nutrition
  4. Meals
  5. Reports
* Supporting folders (`core`, `templates`, `static`, `tests`, `docs`) support the five modules and are not additional functional modules.
* Routes, business logic, database models and external API communication remain separated.
* Existing functionality is not changed without a clear reason; new features and dependencies are discussed and approved before implementation.
* Refactoring is performed when it improves code quality without changing required behaviour.

## 5. Git Workflow

* The shared development branch is **`Development`**; the **`main`** branch holds stable versions.
* Team members work on their own branches and open Pull Requests into `Development` for review.
* `.gitignore` keeps secrets (`.env`), the database file (`calorify.db`), virtual environments and caches out of version control.

## 6. Remaining Tasks

Implementation tasks (outside the scope of this documentation pass — listed here so they are not lost):

1. **Authentication tests** — `tests/test_authentication.py` currently contains only a fixture and no test functions; add registration/login/duplicate-email/invalid-login tests.
2. **Login redirect** — configure `login_manager.login_view = "authentication.login"` so unauthenticated users are redirected to the login page instead of receiving HTTP 401.
3. **Surface the BMI warning in the web flow** — the `POST /profile/` form handler discards the BMI value and warning returned by the service layer.
4. **Fill `README.md` and `.env.example`** — both files exist but are empty; `.env.example` should list `SECRET_KEY`, `GEMINI_API_KEY` and `USDA_API_KEY` (names only, no values).
5. **Pin `pydantic` in `requirements.txt`** — it is imported directly by the Gemini provider but currently installed only as a transitive dependency of `google-genai`.
6. **Database bootstrap step** — document or script `db.create_all()` for fresh setups (no migrations tool is used).
7. **Route-level tests** — add Flask `test_client` tests for the meals, profile and reports endpoints, and mocked-HTTP tests for the provider fallback chain.
8. **Decide on the `charts.py` placeholder** — `app/reports/charts.py` is empty (charts are CSS-rendered); either implement it or remove it. (`app/core/exceptions.py` has since been implemented with the application's custom exception hierarchy.)
9. **CSRF protection** — evaluate adding Flask-WTF (or equivalent) for the form and JSON endpoints.

## 7. Scope Control

Priority remains on required functionality. Barcode scanning, streak tracking, AI diet recommendations, social features, a mobile application, additional nutrition providers and predictive analytics stay out of scope. (Dark mode, originally excluded, was implemented as a small UI preference; the water tracker exists as a browser-local convenience only.)

## 8. Definition of Done

A feature is complete when:

* The required functionality works.
* The code follows the project structure and module boundaries.
* The feature has been tested (automated where practical, manual otherwise).
* Known critical bugs have been fixed.
* Related documentation has been updated.
* The code is ready for integration with the rest of the project.
