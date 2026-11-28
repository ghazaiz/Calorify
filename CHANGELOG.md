# Calorify Changelog

This project uses semantic versioning: `MAJOR.MINOR.PATCH`.

- **Major**: Breaking changes.
- **Minor**: Backward-compatible features.
- **Patch**: Bug fixes, security fixes, and small corrections.

## 1.4.0 - Release and Recovery

- Build versioned source archives with Git revision metadata and SHA-256 checksums.
- Run CI and an isolated staging smoke test before an approved production rollout.
- Add rolling deployment and application rollback, readiness checks, and SQLite backup and restore tools.
- Calculate daily calorie and macro targets from normalized profile inputs. Existing installations can upgrade with `flask --app main init-db`.

## 1.3.0 - Recipe and Label Calculations

- Search for one food or several weighed ingredients in a sentence.
- Scale packaged food from its nutrition label and homemade portions from ingredient totals and the finished batch weight.
- Label database-based results as estimates and show the ingredient breakdown for mixed meals.
- Improve responsive forms, keyboard navigation, and dialog controls. Ship a local set of outline icons.

## 1.2.0 - Database Nutrition and Portions

- Use USDA FoodData Central and Open Food Facts for nutrition lookup.
- Scale grams, milliliters, and documented servings or pieces in search, previews, and meal logging.
- Show incomplete records, unsupported units, and unavailable providers explicitly.
- Improve meal editing, validation feedback, dashboard totals, and profile settings.

## 1.1.1 - Validation and Reporting

- Validate meal, profile, registration, and nutrition inputs before saving or searching.
- Scale fallback nutrition results to the requested grams and handle invalid provider values.
- Combine meal filters, use the local date for water tracking, and render search history as text.
- Aggregate reports in SQL and only load today's meals for the dashboard.
- Add database initialization and application version commands.
- Load configuration before applying defaults and use a random local session key when none is configured.

## 1.1.0 - Exact Match & Reliability

### Added
- Central semantic application version shown in the sidebar.
- Improved food relevance ranking for exact and plain-food searches.

### Fixed
- Egg searches now prefer plain eggs over egg sandwiches or egg custard.
- Fixed the Flask extension circular import.
- Added nutrition, meal, profile, and JSON input validation.
- Corrected Gemini provider integration and provider result normalization.
- Switched password hashing to a supported and reliable method.
