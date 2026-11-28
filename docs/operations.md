# Calorify delivery and operations

## Strategy at a glance

| Area | Calorify strategy |
| --- | --- |
| Project model | Agile, incremental development |
| SCM | Feature branches into `Development`, then reviewed promotion to `main` |
| Distribution | GitHub source repository and versioned ZIP releases with SHA-256 checksums |
| CI | GitHub Actions on branch pushes and pull requests to `Development` and `main` |
| Delivery | Deploy and smoke-test the exact ZIP in an isolated GitHub-hosted staging job |
| Production | Approval-gated rolling deployment on one Linux host with two Gunicorn slots behind Nginx |
| Recovery | Route to the previous healthy release for compatible application issues. Restore verified SQLite snapshots separately if data recovery is required. |
| Backups | 3-2-1. Live data, a mounted external drive, and an independent encrypted offsite repository. Weekly full scan and daily incremental storage. |
| Targets | 24-hour recovery point objective (RPO) and four-hour recovery time objective (RTO) |

## From feature branch to download

1. Create a feature or fix branch from `Development`. Open a PR to `Development` and obtain another developer's review. The workflow installs dependencies for Python 3.11, imports the app, and runs Pytest and shell syntax checks.
2. Use a reviewed PR to promote tested changes from `Development` to `main`. Update `app/version.py` and the changelog as part of the release.
3. After review, tag the approved `main` commit as `vMAJOR.MINOR.PATCH` and push the tag. The workflow requires the tag to match the application version and its commit to be on `main`. It builds the ZIP from a clean checkout and records the full commit in `release.json`. The ZIP excludes live databases, secrets, development caches and virtual environments.
4. The isolated staging job verifies and unpacks that ZIP, installs dependencies, creates a temporary SQLite database, and starts Gunicorn. It tests registration, login, a weighed food search, rejection of an invalid save, saving and retrieving the result, and the weekly report. It then creates, restores, and verifies a SQLite snapshot. The smoke check uses the built-in plain cooked rice reference so staging can run without provider credentials. QA separately checks a live provider and the browser's **Log meal** control before signing off.
5. The Development Lead reviews QA evidence and approves the protected `production` environment. The same artifact goes to the production runner. Once rollout and the proxied health check pass, the workflow attaches the ZIP and checksum to the GitHub release. The tested ZIP is also downloadable as a workflow artifact, including when production is disabled.

To build and verify a local preview:

```sh
python deployment/release.py build dist
python deployment/release.py unpack dist/calorify-<version>-<commit>.zip /tmp/calorify-preview
```

A preview built with uncommitted changes records `dirty: true`. The deployment tool requires a clean release artifact. SHA-256 verifies archive integrity. Obtain both files from the same trusted GitHub workflow or release.

## Hosting and approval setup

Production requires a Linux host with Python 3.11 or later, SQLite 3.35 or later for legacy migrations, Bash, Nginx, systemd, curl, Restic, and a dedicated `calorify` user and group. Provision a durable disk for `/srv/calorify/data` and route the public HTTPS hostname to Nginx at `127.0.0.1:8080` using the host's TLS reverse proxy or load balancer. Run Gunicorn on loopback. Keep both slots on the same host and database volume.

The operator installs the repository configuration on that host:

```sh
sudo install -d -m 0755 /srv/calorify/ops
sudo install -d -m 0750 -o root -g calorify /etc/calorify
sudo install -d -m 0750 -o calorify -g calorify /srv/calorify/{data,releases,slots,state,pre-deploy}
sudo install -d -m 0700 -o calorify -g calorify /srv/calorify/private-backup-input
sudo install -m 0755 deployment/{rollout.sh,backup.sh} /srv/calorify/ops/
sudo install -m 0644 deployment/{release.py,database_backup.py,smoke.py} /srv/calorify/ops/
sudo install -m 0644 deployment/calorify*.service deployment/calorify*.timer /etc/systemd/system/
sudo install -m 0644 deployment/calorify.conf /etc/nginx/conf.d/calorify.conf
printf '%s\n' 'server 127.0.0.1:8001;' | sudo tee /srv/calorify/state/upstream.conf >/dev/null
sudo chmod 0644 /srv/calorify/state/upstream.conf
sudo systemctl daemon-reload
sudo nginx -t
sudo systemctl reload nginx
```

For an existing installation, retain its current upstream file and active slot. The initializer above is for a new host.

Create `/etc/calorify/app.env` as an operator-managed file readable by the service account. Set a long, persistent `SECRET_KEY`, set `DATABASE_URL=sqlite:////srv/calorify/data/calorify.db`, and optionally set `USDA_API_KEY`. Keep the same key across slots. The production unit disables debug mode and requires HTTPS cookies. Set file ownership to root and group to `calorify` with mode `0640`.

In GitHub, protect `Development` and `main` with review and CI requirements. Restrict release tags to authorized maintainers. Configure the `staging` environment for the integration branches and release tags. Configure the `production` environment for release tags, assign the Development Lead as required reviewer, and enable **Prevent self-review**. The plan must support required reviewers for this repository. Use a dedicated self-hosted Linux runner with the `calorify-production` label, running as the deployment account. Give it noninteractive sudo access only to Nginx configuration testing, Nginx reload, and start, stop and enable for the two Calorify units. Once the runner, protected environment, and host have been verified, set repository variable `CALORIFY_PRODUCTION_ENABLED=true`. [GitHub deployment protection rules](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

## Rolling deployment and rollback

The rollout installs the archive alongside the active release, takes a verified pre-deployment SQLite snapshot, and starts the inactive slot. Once the candidate reports the expected version, Nginx sends a small share of requests to it while the current slot continues serving. Health checks run during the overlap. On success, Nginx moves all traffic to the candidate, and the prior slot remains available. On a failed check the script restores the prior routing.

The rollout uses the existing schema for upgrades. Both releases must support that schema for rolling traffic. For a schema change that requires downtime, QA rehearses migration and restoration on a copy. Stop writers in a maintenance window, take and verify a fresh snapshot, run `python -m flask --app main init-db` from the new release using the production configuration, and verify the release before restoring traffic. The previous slot may no longer work after a breaking schema change. Choose an application rollback only when it can read the current data. A database restore is a separate decision because it can discard changes after the snapshot.

For compatible application rollback, run `bash /srv/calorify/ops/rollout.sh rollback` as the deployment account. It verifies the previous slot before redirecting traffic and checks the proxy afterward.

After production deployment, check login, a weighed food search, saving and retrieving the meal, and weekly reports over the public HTTPS URL using a dedicated demonstration account. Confirm `/healthz` reports the expected version. Follow Gunicorn and Nginx logs for failures and repeated HTTP 5xx responses. Enable `calorify-monitor.timer` after initial rollout and route failed probe or service events to the team's configured alert destination. Stop promotion or initiate rollback for recurring readiness errors, failed saves, or unrecoverable report errors. Record the affected version, timestamp and recovery result.

## Backup schedule and verification

The scheduled backup takes a consistent SQLite snapshot using SQLite's backup API. It includes the release archive, checksum, dependency file inside the archive, and the restricted runtime configuration inside the encrypted Restic snapshots. Calorie goals and reports can be recalculated from the database. Browser-local water tracking is outside server backups.

Copy `deployment/backup.env.example` to `/etc/calorify/backup.env` on the host. Configure two independently initialized Restic repositories, one on a mounted external drive and one offsite. Store the Restic password file and offsite access credentials separately from the repositories with access limited to operators. Verify that both repositories can be written to as `calorify`, then enable and start `calorify-backup.timer` and run `calorify-backup.service` once.

The timer runs daily at 02:00 host time. Sunday reads the full backup set. Other days use incremental scans and store changed chunks. Restic deduplicates both, and each successful snapshot can be restored independently. A differential backup would capture changes since the last full baseline. Time to restore and storage requirements led to selecting weekly full scans plus daily incrementals for this project. [Restic backup documentation](https://restic.readthedocs.io/en/stable/040_backup.html).

- Check both snapshots, their timestamps and size, and the service exit status. A failed external copy still allows the offsite attempt.
- Run `restic check` against each repository periodically and use `restic check --read-data` during scheduled integrity drills.
- Rehearse a restore periodically. Record the age of the selected snapshot and elapsed time until the smoke check passes. The targets are 24 hours and four hours respectively. Targets require measured evidence to claim they have been achieved.

## Restore procedure

1. Select the newest verified backup from the external or offsite repository. Restore into a private scratch directory with `restic -r <repository> restore <snapshot-id> --target <scratch>`. Use the matching archive and checksum from that snapshot.
2. Run `python deployment/database_backup.py verify <restored-snapshot.db>` and `python deployment/database_backup.py restore <restored-snapshot.db> <new-db-path>`. The tool refuses to overwrite an existing file.
3. Start the matching application release in isolation with the restored database (use a separate test runtime key for the drill). Verify readiness, login, nutrition lookup, saving, and reports. Reconcile any records created after the selected recovery point.
4. For actual recovery, stop writers and preserve the current database and any SQLite journal or WAL files as a separate recovery copy. Configure the service to point to the verified restored database in the documented location, restore the matching application configuration securely, restart the selected release, repeat smoke tests, and record the elapsed time. [Restic restoration documentation](https://restic.readthedocs.io/en/stable/050_restore.html).
