# Calorify - System Architecture

## 1. Architecture Overview

Calorify will use a modular Flask architecture. The application will be divided into independent modules, each responsible for a specific functionality.

The project will follow:

* Modular Programming
* Separation of Concerns
* Clean Code Principles
* Agile Development
* Continuous Refactoring

## 2. Technology Stack

* Backend: Python and Flask
* Frontend: HTML, CSS, Bootstrap and JavaScript
* Database: SQLite
* ORM: Flask-SQLAlchemy
* Nutrition APIs: USDA FoodData Central and Open Food Facts
* Testing: Pytest
* Development Environment: VS Code
* Version Control: Git and GitHub

## 3. Main Functional Modules

Calorify will contain five main functional modules:

| Module         | Responsibility                                        |
| -------------- | ----------------------------------------------------- |
| Authentication | Registration, login, logout and password security     |
| Profile        | Managing user information and calorie goals           |
| Nutrition      | Searching food and retrieving nutritional information |
| Meals          | Managing meal entries                                 |
| Reports        | Generating daily and weekly summaries and charts      |

The `core` folder is shared infrastructure for configuration, extensions and error handling. It is not considered a functional module.

Templates, static files, tests and documentation are supporting project resources and are not considered functional modules.


## 4. Application Layers

**Routes:** Receive requests, validate input and communicate with services.

**Services:** Handle application logic and coordinate operations.

**Models:** Define database tables and relationships using SQLAlchemy.

**Providers:** Handle communication with external nutrition APIs.

**Templates:** Display application pages using Jinja.

**Static Files:** Store CSS, JavaScript and images.

## 5. Module Communication

1. The user interacts with the frontend.
2. Flask routes receive the request.
3. Routes call the relevant service.
4. Services perform the required application logic.
5. Models interact with the database when necessary.
6. The result is returned to the routes.
7. The frontend displays the response.

The Nutrition module communicates with external providers through its service layer. USDA is the primary provider, while Open Food Facts is the fallback provider.

## 6. Shared Resources

The Core module will manage shared application configuration, database extensions and common error handling.

Modules should use shared resources rather than creating duplicate connections or configurations.

## 7. Development Principles

* Keep modules independent and organised.
* Avoid placing all application logic in main.py.
* Keep routes separate from business logic.
* Avoid unnecessary code duplication.
* Use meaningful names for files, functions and variables.
* Refactor code when necessary without changing expected functionality.
* Write tests for important functionality.
* Obtain approval before introducing additional features or dependencies.
