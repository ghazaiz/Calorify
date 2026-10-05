# Calorify - Project Plan

## 1. Development Methodology

Calorify will be developed using the **Agile methodology**.

The team will work in short development cycles, regularly review progress, test completed features, fix problems, and improve the code through refactoring.

The development process will follow:

**Plan → Design → Develop → Test → Review → Refactor**

## 2. Team Structure

The project team consists of five members with four responsibility areas.

| Role             | Number of Members | Main Responsibilities                              |
| ---------------- | ----------------: | -------------------------------------------------- |
| Developer        |                 2 | Writes, maintains and integrates application code  |
| UI/UX Designer   |                 1 | Plans the user interface and user experience       |
| QA / Tester      |                 1 | Tests features, identifies bugs and verifies fixes |
| Technical Writer |                 1 | Prepares and maintains project documentation       |

All team members will participate in project discussions, sprint reviews and coordination.

## 3. One-Week Development Plan

### Day 1 - Foundation

* Finalize requirements and architecture.
* Set up the Flask development environment.
* Configure SQLite and Flask-SQLAlchemy.
* Create database models.
* Configure the basic Flask application.

### Day 2 - Authentication and Profile

* Implement user registration.
* Implement login and logout.
* Implement secure password hashing.
* Implement user profile.
* Implement calorie-goal calculation.

### Day 3 - Nutrition and Meal Logging

* Integrate USDA FoodData Central.
* Integrate Open Food Facts as a fallback provider.
* Implement food search.
* Display nutritional information.
* Implement adding meals.
* Implement meal categories.
* Implement editing and deleting meals.

### Day 4 - Dashboard and Reports

* Implement the dashboard.
* Display daily calorie information.
* Display protein, carbohydrates and fats.
* Implement weekly summaries.
* Implement charts.

### Day 5 - UI Integration

* Connect application pages.
* Implement navigation.
* Connect forms with backend functionality.
* Add user-friendly error messages.
* Apply basic responsive styling.

### Day 6 - Testing and Refactoring

* Run unit tests.
* Perform integration testing.
* Test nutrition API failures and unavailable results.
* Identify and fix bugs.
* Review code for Clean Code principles.
* Refactor duplicated or unnecessarily complex code.

### Day 7 - Finalisation

* Perform final testing.
* Complete technical documentation.
* Review the complete application.
* Resolve remaining critical bugs.
* Prepare the final demonstration.
* Perform the final Git integration and project review.

## 4. Development Rules

* The application will remain divided into five main functional modules:

  1. Authentication
  2. Profile
  3. Nutrition
  4. Meals
  5. Reports

* Supporting folders such as `core`, `templates`, `static`, `tests` and `docs` will support the five modules and will not be treated as additional functional modules.

* Code will follow Clean Code and modular programming principles.

* Routes, business logic, database models and external API communication will remain separated.

* Existing functionality will not be changed without a clear reason.

* New features will be discussed and approved before implementation.

* Refactoring will be performed when it improves code quality without changing the required behaviour.

## 5. Git Workflow

The team will use Git and GitHub for version control.

The shared development branch is:

`Development`

Team members will work on their own development branches and create Pull Requests when their work is ready for review.

The `main` branch will contain stable project versions.

## 6. Scope Control

Because the project has a one-week development period, priority will be given to the required functionality.

Optional features such as dark mode, barcode scanning, streak tracking, additional nutrition providers, social features and AI-based recommendations will not be implemented unless all required functionality is completed first and the team approves their addition.

## 7. Definition of Done

A feature will be considered complete when:

* The required functionality works.
* The code follows the project structure.
* The feature has been tested.
* Known critical bugs have been fixed.
* The related documentation has been updated when necessary.
* The code is ready for integration with the rest of the project.
