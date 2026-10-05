from flask import Blueprint


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
def home():
    return "Calorify is running!"