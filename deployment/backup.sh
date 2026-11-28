#!/usr/bin/env bash
set -euo pipefail
umask 077

root=/srv/calorify
ops=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
: "${CALORIFY_EXTERNAL_REPO:?Configure the external backup repository}"
: "${CALORIFY_EXTERNAL_MOUNT:?Configure the external drive mount point}"
: "${CALORIFY_OFFSITE_REPO:?Configure the separate offsite backup repository}"
: "${RESTIC_PASSWORD_FILE:?Configure the restic password file}"
[[ $CALORIFY_EXTERNAL_REPO != "$CALORIFY_OFFSITE_REPO" ]]
export RESTIC_PASSWORD_FILE

exec 9>"$root/state/backup.lock"
flock -n 9
slot=$(cat "$root/state/active-slot")
case "$slot" in a|b) ;; *) exit 1 ;; esac
release=$(readlink -f "$root/slots/$slot")
bundle="$root/private-backup-input"
mkdir -p "$bundle"
clean() { rm -f "$bundle"/{calorify.db,release.zip,release.zip.sha256,app.env}; }
trap clean EXIT
clean
python3 "$ops/database_backup.py" snapshot "$root/data/calorify.db" "$bundle/calorify.db"
cp "$release"/release.zip{,.sha256} "$bundle/"
cp /etc/calorify/app.env "$bundle/app.env"

mode=(--tag daily)
if [[ $(date +%u) = 7 ]]; then mode=(--tag weekly --force); fi
failed=0
if mountpoint -q "$CALORIFY_EXTERNAL_MOUNT"; then
    restic --repo "$CALORIFY_EXTERNAL_REPO" backup "${mode[@]}" "$bundle" || failed=1
else
    echo "External backup drive is not mounted." >&2
    failed=1
fi
restic --repo "$CALORIFY_OFFSITE_REPO" backup "${mode[@]}" "$bundle" || failed=1
exit "$failed"
