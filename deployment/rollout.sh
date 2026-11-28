#!/usr/bin/env bash
set -euo pipefail
umask 077

root=${CALORIFY_ROOT:-/srv/calorify}
ops=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
mkdir -p "$root"/{releases,slots,state,pre-deploy}
exec 9>"$root/state/deployment.lock"
flock -n 9

upstream="$root/state/upstream.conf"
active_file="$root/state/active-slot"
proxy=${CALORIFY_PROXY_URL:-http://127.0.0.1:8080}
database="$root/data/calorify.db"
active=$(cat "$active_file" 2>/dev/null || true)
case "$active" in
    a) next=b ;;
    b|'') next=a ;;
    *) echo "Invalid active slot" >&2; exit 1 ;;
esac

port() { if [[ $1 = a ]]; then echo 8001; else echo 8002; fi; }
health() { curl --silent --show-error --fail --max-time 5 "$1/healthz"; }
route() {
    local staged
    staged=$(mktemp "$root/state/upstream.XXXXXX")
    printf '%s\n' "$@" > "$staged"
    mv -f "$staged" "$upstream"
    sudo -n nginx -t && sudo -n systemctl reload nginx
}
verify_version() {
    local reply
    reply=$(health "$1") || return 1
    python3 -c 'import json, sys; data = json.loads(sys.argv[1]); sys.exit(not (data.get("status") == "ok" and data.get("version") == sys.argv[2]))' "$reply" "$2"
}
activate() {
    printf '%s\n' "$1" > "$active_file.new"
    mv -f "$active_file.new" "$active_file"
}

previous_config=$(cat "$upstream")
routing_changed=false
candidate_changed=false
previous_candidate=$(readlink "$root/slots/$next" || true)
work=
on_exit() {
    local code=$?
    if (( code != 0 )) && [[ $routing_changed = true ]]; then
        route "$previous_config" || echo "Routing could not be restored. Check Nginx immediately." >&2
    fi
    if (( code != 0 )) && [[ $candidate_changed = true ]]; then
        sudo -n systemctl stop "calorify@$next.service" || true
        if [[ -n $previous_candidate ]]; then
            ln -sfnT "$previous_candidate" "$root/slots/$next"
            sudo -n systemctl start "calorify@$next.service" || true
        else
            rm -f "$root/slots/$next"
        fi
    fi
    if [[ -n $work ]]; then rm -rf -- "$work"; fi
}
trap on_exit EXIT

case "${1:-}" in
    rollback)
        [[ -n $active && -L "$root/slots/$next" ]] || { echo "No previous slot is available." >&2; exit 1; }
        sudo -n systemctl start "calorify@$next.service"
        version=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$root/slots/$next/release.json")
        verify_version "http://127.0.0.1:$(port "$next")" "$version"
        routing_changed=true
        route "server 127.0.0.1:$(port "$next");"
        verify_version "$proxy" "$version"
        activate "$next"
        echo "Rolled back application traffic to Calorify $version in slot $next."
        ;;
    deploy)
        archive=$(realpath "${2:?Supply a verified release ZIP}")
        work=$(mktemp -d "$root/releases/.incoming.XXXXXX")
        read -r version commit < <(python3 "$ops/release.py" unpack "$archive" "$work/source" --require-clean)
        release="$root/releases/$version-$commit"
        if [[ -e $release ]]; then
            cmp -s "$archive" "$release/release.zip" || { echo "Existing release differs." >&2; exit 1; }
        else
            cp "$archive" "$work/source/release.zip"
            cp "$archive.sha256" "$work/source/release.zip.sha256"
            mv "$work/source" "$release"
        fi
        if [[ -n $active && $(readlink "$root/slots/$active") = "$release" ]]; then
            verify_version "$proxy" "$version"
            echo "Calorify $version ($commit) is already active."
            exit 0
        fi
        python3 -m venv "$release/.venv"
        "$release/.venv/bin/python" -m pip install -r "$release/requirements.txt"

        if [[ -f $database ]]; then
            python3 "$ops/database_backup.py" snapshot "$database" \
                "$root/pre-deploy/calorify-$(date -u +%Y%m%dT%H%M%S%N)-${commit:0:12}.db"
        else
            [[ -z $active ]] || { echo "The existing database is missing." >&2; exit 1; }
            mkdir -p "$root/data"
            (
                cd "$release"
                APP_ENV=staging DATABASE_URL="sqlite:///$database" .venv/bin/python -m flask --app main init-db
            )
        fi

        candidate_changed=true
        sudo -n systemctl stop "calorify@$next.service"
        ln -sfnT "$release" "$root/slots/$next"
        sudo -n systemctl start "calorify@$next.service"
        candidate_url="http://127.0.0.1:$(port "$next")"
        for attempt in {1..30}; do
            if verify_version "$candidate_url" "$version"; then break; fi
            sleep 1
        done
        verify_version "$candidate_url" "$version"
        routing_changed=true
        if [[ -n $active ]]; then
            route "server 127.0.0.1:$(port "$active") weight=4;" \
                  "server 127.0.0.1:$(port "$next") weight=1;"
            for attempt in {1..5}; do
                verify_version "$candidate_url" "$version"
                health "$proxy" >/dev/null
                sleep 2
            done
        fi
        route "server 127.0.0.1:$(port "$next");"
        verify_version "$proxy" "$version"
        sudo -n systemctl enable "calorify@$next.service"
        activate "$next"
        echo "Calorify $version ($commit) is serving in slot $next."
        ;;
    *) echo "Usage: rollout.sh deploy <release.zip> | rollback" >&2; exit 2 ;;
esac
