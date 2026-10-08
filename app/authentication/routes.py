import re
print("Hi")
from flask import Blueprint, request, render_template, redirect
from flask_login import login_user as flask_login_user, logout_user

from app.authentication.service import (
    register_user,
    login_user
)


auth_bp = Blueprint(
    "authentication",
    __name__,
    url_prefix="/auth"
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template(
            "authentication/login.html"
        )

    data = request.form if request.form else request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return render_template(
            "authentication/login.html",
            error="Email and password are required"
        )

    user = login_user(
        email,
        password
    )

    if user is None:
        return render_template(
            "authentication/login.html",
            error="Invalid email or password"
        )

    flask_login_user(user)

    return redirect("/profile/")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template(
            "authentication/register.html"
        )

    data = request.form if request.form else request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return render_template(
            "authentication/register.html",
            error="All fields are required"
        )

    if not re.match(
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

    return redirect("/auth/login")