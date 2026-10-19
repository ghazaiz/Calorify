# Calorify — Software Requirements Specification

## 1. Project Overview

Calorify is a web-based calorie and nutrition tracking application built with Python and Flask.

Registered users can maintain a personal profile, receive a calculated daily calorie and macronutrient target, search for nutrition information, log meals, and review daily and weekly nutrition summaries on a dashboard. Guests can search for nutrition information without creating an account.

The application retrieves nutrition data from external providers instead of maintaining its own food database. Providers are tried in a fixed priority order: **Google Gemini**, then **USDA FoodData Central**, then **Open Food Facts**.

Each requirement below carries a status based on inspection of the codebase:

| Status | Meaning |
| --- | --- |
| Implemented | Present in the code and working as described |
| Partial | Present, but with a documented limitation |
| Planned | Intended behaviour that is not yet implemented |

## 2. Project Objectives

* Help users track their daily food intake.
* Provide nutrition information for searched foods, including mixed South Asian (Desi) dishes such as biryani, pulao, karahi, curry and daal chawal.
* Calculate and display each user's daily calorie and macronutrient targets.
* Allow users to record and manage their meals.
* Provide daily and weekly nutrition summaries and a dashboard.
* Let guests check food nutrition without an account.
* Keep individual users' data separate and secure.

## 3. Target Users

Individuals who want to monitor their food intake through a simple web application. The system supports multiple registered users, and additionally supports anonymous guests for nutrition search only.

## 4. Functional Requirements

### 4.1 Authentication module

| ID | Requirement | Status |
| --- | --- | --- |
| FR-01 | A new user can register with a username, email address and password. | Implemented |
| FR-02 | Registration rejects an email address that is already registered. | Implemented |
| FR-03 | Registration validates the email format and requires a password of at least 8 characters. | Implemented |
| FR-04 | Passwords are stored as secure hashes (Werkzeug `generate_password_hash`), never as plain text. | Implemented |
| FR-05 | A registered user can log in with email and password, and log out. | Implemented |
| FR-06 | Account-specific pages (profile, meals, reports, dashboard) require login. | Partial — protected routes are enforced with `@login_required`, but because no `login_view` is configured in Flask-Login, an unauthenticated request receives an HTTP `401 Unauthorized` response instead of a redirect to the login page. |

### 4.2 Profile module

| ID | Requirement | Status |
| --- | --- | --- |
| FR-07 | A user can create and update a profile with age, sex, height (cm), weight (kg), activity level and weight-management goal (lose / maintain / gain). | Implemented |
| FR-08 | The system calculates and stores a daily calorie target from the profile using the Mifflin–St Jeor equation with activity multipliers (see `docs/architecture.md` §10 for the exact formula). | Implemented |
| FR-09 | For a weight-loss goal, the user can choose a pace of 0.5 kg or 1 kg per week, which adjusts the calorie deficit. | Implemented |
| FR-10 | The system calculates daily protein, carbohydrate and fat targets from the calorie target (21% / 54% / 25% of calories). | Implemented |
| FR-11 | The system calculates BMI and warns when it is below 18.5 or 30 and above. | Partial — calculated in the service layer, but the warning is only returned by the JSON `PUT /profile/` endpoint; the HTML form flow (`POST /profile/`) discards it, so the web page never shows the BMI warning. |
| FR-12 | A logged-in user can change their password (current password required, new password at least 8 characters). | Implemented |
| FR-13 | A user can export their account, profile and meal data as a downloadable JSON file. | Implemented |
| FR-14 | A user can permanently delete their account together with their profile and all meal records. | Implemented |

### 4.3 Nutrition module

| ID | Requirement | Status |
| --- | --- | --- |
| FR-15 | A user can search for a food by name and view its calories, protein, carbohydrates and fats. | Implemented |
| FR-16 | Nutrition providers are tried in priority order: Google Gemini first, then USDA FoodData Central, then Open Food Facts. A provider failure or timeout falls through to the next provider. | Implemented |
| FR-17 | **Guest Nutrition Search**: a visitor without an account can search foods and view nutrition information on a dedicated guest page (`/nutrition/guest`); the search endpoint (`/nutrition/search`) does not require login. Guest search is part of the Nutrition module, not a separate module. | Implemented |
| FR-18 | Saving a search result as a meal, and seeing how a food fits today's goals, require login. | Implemented |
| FR-19 | For mixed dishes (e.g. chicken/mutton/beef biryani, pulao, karahi, curry, daal chawal), the search accepts an optional total dish weight and meat weight and returns nutrition for the **complete dish** (rice/gravy portion + meat portion + oil and other preparation ingredients), with a per-component breakdown. The meat weight is treated as already included in the total and is never double-counted. | Partial — implemented **only through the Gemini provider**, which is instructed via a structured prompt and whose response is validated against a Pydantic schema. The application itself does not recompute or numerically verify the component arithmetic. When Gemini is unavailable and the search falls back to USDA or Open Food Facts, the result is a flat per-100 g value for the closest single match, with no component breakdown and no use of the entered weights. |
| FR-20 | The search accepts natural-language entries including quantities in the text (e.g. "300g chicken biryani with 150g chicken"). | Partial — supported only via the Gemini provider's prompt; fallback providers treat the input as a plain search term. |
| FR-21 | Mixed-dish results are clearly marked as estimates, because recipes and preparation methods vary. | Implemented — Gemini results carry an `estimate` flag, shown in the UI as an "~ Estimated" chip. |
| FR-22 | When a food cannot be found or all providers fail, the user sees a clear error message. | Implemented |

### 4.4 Meals module

| ID | Requirement | Status |
| --- | --- | --- |
| FR-23 | A logged-in user can add a meal with food name, meal type, quantity, serving unit, calories, protein, carbohydrates, fats and an optional date (defaults to today). | Implemented |
| FR-24 | Meals are categorised as breakfast, lunch, dinner or snack; any other category is rejected. | Implemented |
| FR-25 | A user can view their saved meals, newest first, with search and category filtering in the UI. | Implemented |
| FR-26 | A user can edit and delete their own meal entries. | Implemented |
| FR-27 | A user can only read or modify their own meals; a meal belonging to another user behaves as not found (HTTP 404). | Implemented |
| FR-28 | A saved meal or a nutrition search result can be re-logged for today with one click. | Implemented |

### 4.5 Reports module

| ID | Requirement | Status |
| --- | --- | --- |
| FR-29 | The system provides a daily summary of calories, protein, carbohydrates, fats and meal count for a given date (`GET /reports/daily`, JSON). | Implemented |
| FR-30 | The system provides a weekly report covering the last 7 days with per-day totals. | Implemented |
| FR-31 | The weekly report page shows average intake, change versus the previous week, days on target, average protein and carbohydrates, a macro calorie split, and textual insights. | Implemented |
| FR-32 | The dashboard shows today's intake against the user's calorie and macro goals, remaining calories, today's meals, and a 7-day mini chart. | Implemented |
| FR-33 | Nutrition information is presented with charts (calorie bar chart with goal line, macro split donut, progress rings). | Implemented — rendered with CSS and Jinja templates; no JavaScript charting library is used. |
| FR-34 | A user who has not completed a profile is redirected from the dashboard to the profile page. | Implemented |

### 4.6 Cross-cutting

| ID | Requirement | Status |
| --- | --- | --- |
| FR-35 | Invalid input (missing fields, non-numeric values, malformed dates, invalid meal types) produces a clear error message instead of a crash. | Implemented |
| FR-36 | API-style clients that send `Accept: application/json` receive JSON responses; browsers receive HTML pages from the same endpoints. | Implemented |

## 5. Non-Functional Requirements

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-01 | **Performance** — external provider calls are time-boxed: Gemini is capped at 15 seconds (SDK timeout plus a thread-pool timeout, single attempt), USDA and Open Food Facts at 10 seconds each. A slow provider falls through to the next one rather than hanging the request. | Implemented |
| NFR-02 | **Reliability** — failure of any external nutrition API must not crash the application; provider errors are caught and the fallback chain continues. | Implemented |
| NFR-03 | **Security: passwords** — stored only as salted hashes via Werkzeug. | Implemented |
| NFR-04 | **Security: secrets** — API keys (`GEMINI_API_KEY`, `USDA_API_KEY`) and `SECRET_KEY` are read from environment variables / a `.env` file that is excluded from version control. | Partial — implemented, but `SECRET_KEY` falls back to a hard-coded development default when the environment variable is missing, and the application's forms have no CSRF protection (Flask-WTF is not used). Acceptable for a course project; documented as a limitation. |
| NFR-05 | **Maintainability** — modular programming, separation of concerns (routes / services / models / providers), consistent naming. | Implemented |
| NFR-06 | **Usability** — clear navigation, readable information, understandable error messages, responsive layout, light/dark theme. | Implemented |
| NFR-07 | **Compatibility** — works in commonly used modern web browsers; no server-side browser dependencies. | Implemented (manually verified only) |
| NFR-08 | **Testing** — important application logic is covered by automated Pytest tests. | Partial — service-layer and schema tests exist and pass; the Authentication module and the HTTP routes currently have no automated tests (see `docs/testing.md`). |

## 6. Main Functional Modules

Calorify contains exactly five main functional modules:

1. **Authentication** — registration, login, logout, password hashing.
2. **Profile** — body details, goals, calorie/macro targets, account management.
3. **Nutrition** — food search, provider fallback, mixed-dish estimates, guest search.
4. **Meals** — meal logging and management.
5. **Reports** — daily/weekly summaries and the dashboard.

Supporting packages and folders — `core` (configuration, extensions, shared helpers), `templates`, `static`, `tests` and `docs` — are project infrastructure, not additional functional modules.

## 7. Technology Requirements

| Area | Technology |
| --- | --- |
| Language | Python 3.11 |
| Web framework | Flask 3.1 |
| ORM / database | Flask-SQLAlchemy 3.1, SQLAlchemy 2.1, SQLite |
| Authentication | Flask-Login 0.6 |
| Nutrition providers | Google Gemini (`google-genai` SDK), USDA FoodData Central API, Open Food Facts API |
| HTTP client | `requests` |
| Validation | Pydantic (response schema for Gemini; installed as a dependency of `google-genai`) |
| Frontend | Jinja2 templates, Bootstrap 5.3 (CDN), custom CSS, vanilla JavaScript |
| Configuration | `python-dotenv` (`.env` file) |
| Testing | Pytest 9 |
| Version control | Git and GitHub |

## 8. Project Scope

### Included (implemented)

User authentication, profiles with calculated calorie/macro goals, nutrition search with a three-provider fallback chain, mixed Desi-dish estimates via Gemini, guest nutrition search, meal logging with categories, daily summaries, weekly reports with CSS-rendered charts and insights, a dashboard, password change, data export and account deletion, and a light/dark theme.

### Implemented beyond the original scope

* **Dark mode** (originally excluded) — a theme toggle stored in the browser's `localStorage`.
* **Water tracker** on the dashboard — stored per-day in the browser's `localStorage` only; it is not saved to the database and does not sync across devices.
* **Recent / session search history** on the nutrition pages — stored in browser `localStorage` / `sessionStorage` only.

### Excluded

Barcode scanning, streak tracking, AI diet recommendations, social features, a mobile application, additional nutrition providers, and predictive analytics remain out of scope.

## 9. Disclaimer

Calorie and macronutrient targets are general estimates derived from standard equations, and nutrition values for mixed dishes are model-based estimates that vary with recipe and preparation. Calorify's output is not medical or dietary advice.
