import re
from flask import Blueprint, request, jsonify
from flask_login import login_user as flask_login_user, logout_user

from app.authentication.service import register_user, login_user 


auth_bp = Blueprint("authentication", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    
    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400
   
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"message": "Please enter a valid email address"}), 400

    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters long"}), 400    
    
    user = register_user(username, email, password)

    if user is None:
        return jsonify({"message": "Email already registered"}), 409

    return jsonify({"message": "Registration successful"}), 201
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = login_user(email, password)

    if user is None:
        return jsonify({"message": "Invalid email or password"}), 401

    flask_login_user(user)

    return jsonify({"message": "Login successful"}), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()

    return jsonify({"message": "Logout successful"}), 200