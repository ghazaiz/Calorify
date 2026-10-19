from datetime import date, datetime

from flask import Blueprint, jsonify, request, render_template, redirect
from flask_login import login_required, current_user

from app.reports.service import (
    get_daily_report,
    get_weekly_report
)
from app.profile.models import Profile


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


@reports_bp.route("/daily", methods=["GET"])
@login_required
def daily_report():
    report_date = request.args.get("date")

    selected_date = None

    if report_date:
        from datetime import date

        try:
            selected_date = date.fromisoformat(report_date)
        except ValueError:
            return jsonify({
                "message": "Invalid date format. Use YYYY-MM-DD"
            }), 400

    report = get_daily_report(
        current_user.user_id,
        selected_date
    )

    return jsonify(report), 200


@reports_bp.route("/weekly", methods=["GET"])
@login_required
def weekly_report():
    report = get_weekly_report(
        current_user.user_id
    )

    if request.accept_mimetypes.best == "text/html":
        return render_template("reports/reports.html", report=report)

    return jsonify({
        "report": report
    }), 200


@reports_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    profile = Profile.query.filter_by(
        user_id=current_user.user_id
    ).first()

    if profile is None:
        return redirect("/profile/")

    today = get_daily_report(
        current_user.user_id
    )

    calorie_goal = profile.daily_calorie_target
    protein_goal = profile.protein_target
    carbohydrates_goal = profile.carbohydrates_target
    fats_goal = profile.fats_target

    return render_template(
        "dashboard/dashboard.html",
        today=today,
        today_display=(
            datetime.strptime(today["date"], "%Y-%m-%d").strftime("%A")
            + f", {datetime.strptime(today['date'], '%Y-%m-%d').day} "
            + datetime.strptime(today["date"], "%Y-%m-%d").strftime("%B")
        ),
        calorie_goal=calorie_goal,
        protein_goal=protein_goal,
        carbohydrates_goal=carbohydrates_goal,
        fats_goal=fats_goal
    )