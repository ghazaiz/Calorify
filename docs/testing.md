# Calorify - Testing Strategy

## 1. Testing Approach

Calorify will use automated and manual testing to verify that the application works correctly.

Testing will be performed throughout development rather than only at the end of the project.

The testing process will follow:

**Develop → Test → Fix → Retest → Refactor**

## 2. Testing Framework

The project will use **Pytest** for automated testing.

External nutrition APIs will be mocked during tests so that tests do not depend on real API responses.

## 3. Types of Testing

### 3.1 Unit Testing

Unit tests will verify individual functions and services separately.

Examples:

* Password hashing and verification
* Calorie target calculation
* Meal calculations
* Nutrition data processing
* Input validation

### 3.2 Integration Testing

Integration tests will verify that different parts of the application work together correctly.

Examples:

* Registration and database storage
* Login and authentication
* Profile updates
* Adding meals to the database
* Retrieving daily meal summaries

### 3.3 API Testing

Nutrition API communication will be tested using mocked responses.

The tests will cover:

* Successful API response
* Food not found
* Invalid API response
* API timeout or failure
* Fallback from USDA to Open Food Facts

### 3.4 Manual Testing

Important user workflows will also be tested manually through the web interface.

Examples:

* Registering a new account
* Logging in and logging out
* Updating a profile
* Searching for food
* Adding, editing and deleting meals
* Viewing daily information
* Viewing weekly reports

## 4. Main Test Cases

| Test Area      | Test                                   |
| -------------- | -------------------------------------- |
| Authentication | User can register                      |
| Authentication | Duplicate email is rejected            |
| Authentication | User can log in                        |
| Authentication | Invalid login is rejected              |
| Profile        | User can update profile                |
| Profile        | Calorie target is calculated           |
| Nutrition      | Food search returns nutrition data     |
| Nutrition      | API failure is handled                 |
| Nutrition      | Fallback provider is used              |
| Meals          | User can add a meal                    |
| Meals          | User can edit their meal               |
| Meals          | User can delete their meal             |
| Meals          | User cannot access another user's meal |
| Reports        | Daily totals are calculated correctly  |
| Reports        | Weekly summary is generated            |
| Reports        | Charts receive correct data            |

## 5. Test Data

Tests will use separate test data and a test database where required.

Real user data will not be used for automated testing.

External API responses will be mocked to make tests predictable and repeatable.

## 6. Error Testing

The application will be tested for common errors, including:

* Invalid form data
* Missing required fields
* Incorrect login information
* Food not found
* External API failure
* Database errors
* Unauthorized access

The application should display a clear error message instead of crashing.

## 7. Security Testing

Security-related tests will verify that:

* Passwords are never stored as plain text.
* Users cannot access another user's private data.
* Protected pages require authentication.
* API keys are not stored directly in source code.

## 8. Code Coverage

The team will aim for approximately **80% automated test coverage** for important application logic.

Coverage will be reviewed during the testing and refactoring phase.

## 9. Definition of Testing Completion

Testing for a feature will be considered complete when:

* The expected functionality works.
* Important error cases have been tested.
* Automated tests pass.
* Relevant integration tests pass.
* Critical bugs have been fixed.
* The feature does not break existing functionality.

## 10. Testing and Refactoring

After testing, the team will review the code for:

* Duplicate code
* Unnecessary complexity
* Poor naming
* Large functions
* Incorrect separation of responsibilities

Refactoring will improve the code structure without changing the expected behaviour of the application.
