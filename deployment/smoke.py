"""Exercise a running Calorify instance from signup to saved nutrition."""

import argparse
import secrets
import sys

import requests


JSON = {"Accept": "application/json"}
NUTRIENTS = ("calories", "protein", "carbohydrates", "fats")


def request(session, method, base, path, expected=200, **kwargs):
    response = session.request(method, base + path, timeout=15, allow_redirects=False, **kwargs)
    if response.status_code != expected:
        raise RuntimeError(f"{method} {path} returned {response.status_code}, expected {expected}.")
    return response


def smoke(base, version, health_only):
    with requests.Session() as session:
        ready = request(session, "GET", base, "/healthz").json()
        if ready.get("status") != "ok" or (version and ready.get("version") != version):
            raise RuntimeError("The expected release is not ready.")
        print(f"Ready: {ready['version']}")
        if health_only:
            return
        request(session, "GET", base, "/nutrition/guest")
        suffix = secrets.token_hex(8)
        account = {"username": f"smoke-{suffix}", "email": f"smoke-{suffix}@example.invalid",
                   "password": secrets.token_urlsafe(24)}
        request(session, "POST", base, "/auth/register", data=account)
        request(session, "POST", base, "/auth/login", 302, data=account)
        try:
            food = request(session, "GET", base, "/nutrition/search", headers=JSON,
                           params={"food": "plain cooked rice", "quantity": 150, "unit": "g"}).json()["food"]
            if food["quantity_grams"] != 150 or food["calories"] != 195:
                raise RuntimeError("Nutrition lookup returned an unexpected portion.")
            meal = {
                "food_name": food["name"], "meal_type": "lunch",
                "quantity": food["quantity"], "serving_unit": food["quantity_unit"],
                **{key: food[key] for key in NUTRIENTS},
            }
            request(session, "POST", base, "/meals/", 400, headers=JSON, json={**meal, "quantity": 0})
            saved = request(session, "POST", base, "/meals/", 201, headers=JSON, json=meal).json()["meal"]
            meals = request(session, "GET", base, "/meals/", headers=JSON).json()["meals"]
            if meals != [saved] or saved["calories"] != food["calories"]:
                raise RuntimeError("The saved nutrition result was missing or changed.")
            request(session, "GET", base, "/reports/weekly")
            print("Login, weighed nutrition lookup, invalid save, valid save, retrieval and report passed.")
        finally:
            request(session, "POST", base, "/profile/delete", 302)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--version")
    parser.add_argument("--health-only", action="store_true")
    args = parser.parse_args()
    try:
        smoke(args.url.rstrip("/"), args.version, args.health_only)
    except (RuntimeError, requests.RequestException, KeyError, ValueError) as error:
        sys.exit(f"Smoke check failed: {error}")
