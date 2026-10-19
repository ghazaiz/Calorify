import re
from collections.abc import Mapping

from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_user as flask_login_user, logout_user

from app.authentication.service import (
    register_user,
    login_user
)
from app.profile.models import Profile

auth_bp = Blueprint(
    "authentication",
    __name__,
    url_prefix="/auth"
)


def _request_data() -> Mapping[str, object]:
    data = request.form or request.get_json(silent=True)
    return data if isinstance(data, Mapping) else {}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template(
            "authentication/login.html"
        )

    data = _request_data()

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return render_template(
            "authentication/login.html",
            error="Email and password are required"
        )

    user = login_user(
        email.strip(),
        password
    )

    if user is None:
        return render_template(
            "authentication/login.html",
            error="Invalid email or password"
        )

    flask_login_user(user)

    profile = Profile.query.filter_by(user_id=user.user_id).first()
    destination = "reports.dashboard" if profile else "profile.profile"
    return redirect(url_for(destination))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template(
            "authentication/register.html"
        )

    data = _request_data()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if (
        not isinstance(username, str)
        or not isinstance(email, str)
        or not isinstance(password, str)
        or not username.strip()
        or not email.strip()
        or not password
    ):
        return render_template(
            "authentication/register.html",
            error="All fields are required"
        )

    email = email.strip()
    username = username.strip()

    if not re.fullmatch(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        email
    ):
        return render_template(
            "authentication/register.html",
            error="Please enter a valid email address"
        )

    if len(password) < 8:
        return render_template(
            "authentication/register.html",
            error="Password must be at least 8 characters long"
        )

    user = register_user(
        username,
        email,
        password
    )

    if user is None:
        return render_template(
            "authentication/register.html",
            error="Email already registered"
        )

    return render_template(
        "authentication/login.html",
        success="Account created successfully. Please log in."
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():

    logout_user()

    return redirect(url_for("authentication.login"))