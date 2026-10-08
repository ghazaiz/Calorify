# Calorify - Database Design

## 1. Database Technology

Calorify will use SQLite as its database and Flask-SQLAlchemy as its ORM (Object Relational Mapper).

## 2. Database Tables

### 2.1 Users Table

Stores account and authentication information.

| Field         | Description              | Constraint       |
| ------------- | ------------------------ | ---------------- |
| user_id       | Unique user identifier   | Primary Key      |
| username      | User's name              | Required         |
| email         | User's email address     | Unique, Required |
| password_hash | Securely hashed password | Required         |
| created_at    | Account creation date    | Required         |

### 2.2 Profiles Table

Stores personal information and daily calorie goals.

| Field                | Description                      | Constraint          |
| -------------------- | -------------------------------- | ------------------- |
| profile_id           | Unique profile identifier        | Primary Key         |
| user_id              | Associated user                  | Foreign Key, Unique |
| age                  | User's age                       | Required            |
| sex                  | Used for calorie calculations    | Required            |
| height               | Height in centimetres            | Required            |
| weight               | Weight in kilograms              | Required            |
| activity_level       | User's activity level            | Required            |
| goal                 | Weight loss, maintenance or gain | Required            |
| daily_calorie_target | Daily calorie goal               | Required            |

### 2.3 Meals Table

Stores food and meal information logged by users.

| Field         | Description                       | Constraint  |
| ------------- | --------------------------------- | ----------- |
| meal_id       | Unique meal identifier            | Primary Key |
| user_id       | Associated user                   | Foreign Key |
| food_name     | Name of the food                  | Required    |
| meal_type     | Breakfast, lunch, dinner or snack | Required    |
| quantity      | Amount consumed                   | Required    |
| serving_unit  | Unit such as grams or pieces      | Required    |
| calories      | Calories consumed                 | Required    |
| protein       | Protein in grams                  | Required    |
| carbohydrates | Carbohydrates in grams            | Required    |
| fats          | Fats in grams                     | Required    |
| date          | Date the meal was consumed        | Required    |
| created_at    | Record creation date              | Required    |

## 3. Table Relationships

* One user can have only one profile.
* One user can have multiple meal records.
* Every profile belongs to one user.
* Every meal record belongs to one user.

## 4. Primary and Foreign Keys

* `users.user_id`: Primary Key.
* `profiles.profile_id`: Primary Key.
* `profiles.user_id`: Foreign Key referencing `users.user_id`, with a unique constraint.
* `meals.meal_id`: Primary Key.
* `meals.user_id`: Foreign Key referencing `users.user_id`.

## 5. Data Integrity and Security

* Email addresses must be unique.
* Passwords must be stored as secure hashes, never as plain text.
* Foreign keys will maintain relationships between tables.
* Users must only access their own profile and meal records.
* Each meal will store a snapshot of its nutritional values so historical records remain unchanged if an external nutrition provider updates its data.

## 6. Database Scope

The initial version will use three main tables: Users, Profiles and Meals.

A separate food catalogue will not be maintained because nutritional information will be retrieved from external APIs.
