# Calorify course submission evidence

The TaskFlow document provides an example project format. The Calorify distribution plan supplies the operating choices for this project. `Calorify_CICD_Class_Activity.docx` and `Calorify_SCM_Assignment_3.docx` contain the same CI/CD activity.

| Course topic | Calorify implementation or project practice | Evidence |
| --- | --- | --- |
| Problem, users, scope and acceptance criteria | Calorie and meal tracking for members, with guest food lookup | [Requirements](requirements.md) |
| Project model, team roles and delivery increments | Agile, incremental development with feature branches and review | [Project plan](project_plan.md) |
| Architecture, technology stack and request flow | Flask routes and services, Jinja and static UI, SQLAlchemy and SQLite | [Architecture](architecture.md) |
| Data model and normalization | Separate users, profiles and meal snapshots. Derived goals are calculated on read. | [Database design](database_design.md) |
| Readable construction and input validation | Named service functions and explicit input validation in the application modules | Application modules and Pytest coverage |
| Source control and reviews | Feature PRs into `Development`, release PR into `main`, required CI and review policy | [PR template](../.github/pull_request_template.md) and actual PR records |
| Unit, persistence, route and integration tests | Isolated SQLite fixtures, provider mocks, packaged-app HTTP smoke test | [Testing](testing.md), [smoke test](../deployment/smoke.py) |
| Build and distribution | GitHub distribution, SemVer, ZIP, commit manifest and checksum | [Release builder](../deployment/release.py) and Actions artifact |
| Delivery and approval | Artifact runs on Gunicorn in isolated staging. QA validates the result and the Development Lead approves production. | [Workflow](../.github/workflows/development.yml), staging job output and production approval record |
| Deployment, monitoring and rollback | Two-slot rolling rollout, health checks, periodic probe and previous-slot rollback | [Operations runbook](operations.md), [rollout script](../deployment/rollout.sh) |
| Backup and recovery | 3-2-1 schedule, verified SQLite snapshots, encrypted Restic copies and restoration drill | [Operations runbook](operations.md), [database tool](../deployment/database_backup.py) |

For the bug-fix lab, choose a real Calorify defect or reproduce a controlled validation regression on a disposable feature branch. Capture the issue with steps and expected behavior, the failing test, the fix, the reviewed PR and the passing CI run. The reviewed correction is the change that goes into `Development`.

Collect and date the following where the submission asks for evidence:

- Commit, version and PR review links for the selected Calorify feature.
- CI run link, artifact manifest and checksum, and staging log showing the resulting meal persisted.
- QA sign-off, production approval and deployment URL if a host has been configured.
- Monitoring and smoke-test output, rollback result, and backup and restore drill times when performed.

The workflow and scripts are version-controlled. GitHub review settings, hosted production, and both external backup destinations require the team's account and infrastructure configuration. Record operational results from actual runs.
