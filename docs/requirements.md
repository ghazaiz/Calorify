# Calorify - Software Requirements Specification

## 1. Project Overview

Calorify is a web-based calorie and nutrition tracking application developed using Python and Flask.

The system will allow users to create accounts, maintain their profiles, search for food nutrition information, log meals, monitor their daily calorie intake and view weekly nutrition reports.

The application will use external nutrition APIs instead of maintaining its own food database.

## 2. Project Objectives

The main objectives of Calorify are to:

* Help users track their daily food intake.
* Provide nutritional information for searched foods.
* Calculate and display a user's daily calorie target.
* Allow users to record and manage their meals.
* Provide daily and weekly nutrition summaries.
* Present nutrition information in an understandable dashboard.
* Keep individual users' data separate and secure.

## 3. Target Users

The system is designed for individuals who want to monitor their food intake and nutritional information through a simple web application.

The system will support multiple registered users.

## 4. Functional Requirements

### FR-01: User Registration

The system shall allow a new user to create an account using a username, email address and password.

### FR-02: User Login and Logout

The system shall allow registered users to securely log in and log out.

### FR-03: User Profile

The system shall allow users to create and update their profile information, including:

* Age
* Sex
* Height
* Weight
* Activity level
* Goal

### FR-04: Daily Calorie Target

The system shall calculate and store a user's daily calorie target based on their profile information.

### FR-05: Food Search

The system shall allow users to search for food and obtain nutritional information.

### FR-06: USDA Nutrition Provider

The system shall use USDA FoodData Central as the primary external nutrition provider.

### FR-07: Open Food Facts Fallback

The system shall use Open Food Facts as a fallback when a suitable result cannot be obtained from the primary provider.

### FR-08: Nutrition Information

The system shall display relevant nutritional information including:

* Calories
* Protein
* Carbohydrates
* Fats

### FR-09: Add Meal

The system shall allow users to add food to their meal records.

Each meal shall include:

* Food name
* Meal type
* Quantity
* Serving unit
* Calories
* Protein
* Carbohydrates
* Fats
* Date

### FR-10: Meal Categories

The system shall allow meals to be categorized as:

* Breakfast
* Lunch
* Dinner
* Snack

### FR-11: Edit Meal

The system shall allow users to edit their own meal records.

### FR-12: Delete Meal

The system shall allow users to delete their own meal records.

### FR-13: Daily Summary

The system shall display the user's daily:

* Calorie intake
* Protein intake
* Carbohydrate intake
* Fat intake

### FR-14: Calories Remaining

The system shall calculate and display the remaining calories based on the user's daily calorie target and logged meals.

### FR-15: Weekly Reports

The system shall provide weekly summaries of the user's calorie and nutritional intake.

### FR-16: Charts

The system shall present relevant nutrition information using charts.

### FR-17: Dashboard

The system shall provide a dashboard where users can view important information such as their calorie target, daily intake, remaining calories and nutrition summary.

### FR-18: Error Handling

The system shall display clear and user-friendly messages when:

* Food cannot be found.
* An external API is unavailable.
* An API request fails.
* Invalid information is entered.
* A requested operation cannot be completed.

### FR-19: User Data Isolation

The system shall ensure that users can access and modify only their own profile and meal records.

## 5. Non-Functional Requirements

### NFR-01: Performance

Food searches should normally return a response within a reasonable amount of time. If an external provider takes too long to respond, the system shall display an appropriate error message.

### NFR-02: Reliability

Failure of an external nutrition API shall not cause the entire application to crash.

### NFR-03: Security

User passwords shall be stored using secure password hashing rather than plain text.

### NFR-04: API Key Security

API keys and other sensitive configuration values shall be stored in environment variables and shall not be committed to GitHub.

### NFR-05: Maintainability

The system shall use modular programming, separation of concerns and Clean Code principles.

### NFR-06: Usability

The application shall provide clear navigation, readable information and understandable error messages.

### NFR-07: Compatibility

The application should work on commonly used modern web browsers and operating systems.

### NFR-08: Testing

Important application functionality shall be covered by automated tests using Pytest.

### NFR-09: Refactoring

The code shall be reviewed and refactored when necessary to improve readability, maintainability and reduce duplication without changing required functionality.

## 6. Main Functional Modules

Calorify will contain five main functional modules:

1. Authentication
2. Profile
3. Nutrition
4. Meals
5. Reports

Supporting folders such as `core`, `templates`, `static`, `tests` and `docs` are project infrastructure and are not considered additional functional modules.

## 7. Technology Requirements

The project will use:

* Python
* Flask
* Flask-SQLAlchemy
* SQLite
* HTML
* CSS
* Bootstrap
* JavaScript
* USDA FoodData Central API
* Open Food Facts API
* Pytest
* Git and GitHub

## 8. Project Scope

### Included

The first version will include user authentication, profiles, calorie goals, nutrition search, meal logging, daily summaries, weekly reports, charts and a dashboard.

### Excluded

The following features are outside the current project scope:

* Dark mode
* Barcode scanning
* Streak tracking
* AI diet recommendations
* Social features
* Mobile application
* Additional nutrition providers
* Predictive analytics

Optional features may only be considered if all required functionality is completed and the team agrees to include them.
