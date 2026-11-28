# Calorify project plan

## Development model

**Agile, incremental development.** Each increment delivers a working slice of Calorify. The team prioritizes the backlog, defines acceptance criteria, builds and tests a small change, reviews it in a pull request, and uses feedback to plan the next increment. Iteration reviews evaluate the running application and the evidence from tests.

| Increment | Deliverable | Evidence in the repository |
| --- | --- | --- |
| 1 | Project foundation and account registration, login and logout | Flask application factory, SQLite schema, Authentication module and tests |
| 2 | Profile setup, nutrition targets and meal journal | Profile and Meals modules, validation and persistence tests |
| 3 | Calorie Check, guest lookup and progress reports | Nutrition and Reports modules, provider fallback tests and dashboard |
| 4 | Sentence search, label and recipe calculations, responsive UI | Calorie Check forms, portion tests and release notes |
| 5 | Release automation, staged smoke tests and recovery | CI/CD workflow, versioned archives, deployment files and operations runbook |

The table describes product increments. PR links, review decisions, CI run URLs and deployment timestamps are captured when a team member performs the actual activity.

## Team responsibilities

| Role | Responsibility |
| --- | --- |
| Two developers | Implement features, review each other's pull requests, and integrate changes. One acts as Development Lead and approves production releases. |
| UI/UX designer | Check responsive layouts, keyboard navigation, forms and feedback. |
| QA tester | Verify acceptance criteria, examine staging results and record release evidence. |
| Technical writer | Update release notes, requirements, setup instructions and runbooks. |

## Software configuration management

Use **feature branching** with a shared integration branch. Start each feature or fix from `Development` and open a PR back to `Development`. Review correctness, validation, data isolation, tests and documentation with a second developer. Promote an approved integration through a PR from `Development` to `main`. Keep `main` releasable. The GitHub repository owner configures required reviews and the **CI - Python 3.11 tests** check on both branches.

Version source releases with **Semantic Versioning**. Record behavior changes in the changelog and set the version centrally in `app/version.py`. Tag the reviewed commit on `main` as `vMAJOR.MINOR.PATCH`. GitHub distributes the code and the workflow distributes a ZIP identified by version and commit, with a SHA-256 checksum. The [operations runbook](operations.md) describes delivery, approval, production, monitoring, and rollback.

## Definition of done

- Acceptance criteria have been met and the relevant tests pass.
- Routes, business logic, persistence and templates follow the existing module boundaries.
- User input is validated, data access is parameterized, and secrets are managed outside version control.
- Another developer has reviewed the PR and review feedback has been addressed.
- The affected documentation and changelog have been updated.
- Releases have a verified staging run, QA sign-off and approval evidence before production.

## Evidence for the course submission

Use the [project evidence guide](submission_evidence.md) to map each course deliverable to actual Calorify files and record links to team reviews, Actions runs, and operational checks as they happen.
