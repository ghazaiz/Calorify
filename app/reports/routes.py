from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, render_template, redirect
from flask_login import login_required, current_user

from app.core.http import wants_json
from app.reports.service import (
    get_daily_report,
    get_weekly_report
)
from app.profile.models import Profile
from app.profile.service import get_bmi_summary
from app.meals.service import get_user_meals


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


def build_weekly_stats(report, previous_report, profile):
    """Compute the stats and insights shown on the weekly report page."""
    calorie_goal = profile.daily_calorie_target if profile else 0
    protein_goal = profile.protein_target if profile else 0

    logged_days = [day for day in report if day["calories"] > 0]

    avg_intake = round(
        sum(day["calories"] for day in logged_days) / len(logged_days)
    ) if logged_days else 0

    previous_logged = [
        day for day in previous_report if day["calories"] > 0
    ]
    previous_avg = (
        sum(day["calories"] for day in previous_logged) / len(previous_logged)
    ) if previous_logged else 0

    intake_change = round(
        ((avg_intake - previous_avg) / previous_avg) * 100
    ) if previous_avg else None

    on_target_days = [
        day for day in logged_days
        if calorie_goal and day["calories"] <= calorie_goal
    ]

    avg_protein = round(
        sum(day["protein"] for day in logged_days) / len(logged_days)
    ) if logged_days else 0

    avg_carbohydrates = round(
        sum(day["carbohydrates"] for day in logged_days) / len(logged_days)
    ) if logged_days else 0

    # Macro split by calorie contribution across the week
    protein_calories = sum(day["protein"] for day in report) * 4
    carbohydrate_calories = sum(day["carbohydrates"] for day in report) * 4
    fat_calories = sum(day["fats"] for day in report) * 9
    total_macro_calories = (
        protein_calories + carbohydrate_calories + fat_calories
    )

    macro_split = {
        "protein": round(protein_calories / total_macro_calories * 100),
        "carbohydrates": round(
            carbohydrate_calories / total_macro_calories * 100
        ),
        "fats": round(fat_calories / total_macro_calories * 100)
    } if total_macro_calories else None

    insights = []

    if on_target_days:
        best_day = min(on_target_days, key=lambda day: day["calories"])
        best_day_name = date.fromisoformat(best_day["date"]).strftime("%A")
        insights.append({
            "icon": "check",
            "text": f"{best_day_name} was your lightest day on target "
                    f"with {round(best_day['calories'])} kcal."
        })

    if protein_goal and logged_days:
        protein_gap = round(protein_goal - avg_protein)
        if protein_gap > 5:
            insights.append({
                "icon": "info",
                "text": f"Protein averaged {protein_gap} g under your goal. "
                        "A yogurt or egg snack would close the gap."
            })
        elif protein_gap <= 0:
            insights.append({
                "icon": "check",
                "text": "You hit your protein goal on average this week."
            })

    over_days = [
        day for day in logged_days
        if calorie_goal and day["calories"] > calorie_goal
    ]
    if over_days:
        insights.append({
            "icon": "info",
            "text": f"You went over your calorie goal on "
                    f"{len(over_days)} day{'s' if len(over_days) > 1 else ''}."
        })

    if not logged_days:
        insights.append({
            "icon": "info",
            "text": "No meals logged this week yet. "
                    "Log a meal to start seeing insights."
        })

    return {
        "avg_intake": avg_intake,
        "intake_change": intake_change,
        "on_target_days": len(on_target_days),
        "logged_days": len(logged_days),
        "avg_protein": avg_protein,
        "avg_carbohydrates": avg_carbohydrates,
        "protein_gap": round(protein_goal - avg_protein) if protein_goal else None,
        "macro_split": macro_split,
        "insights": insights
    }


@reports_bp.route("/weekly", methods=["GET"])
@login_required
def weekly_report():
    report = get_weekly_report(
        current_user.user_id
    )

    if not wants_json():
        profile = Profile.query.filter_by(
            user_id=current_user.user_id
        ).first()

        end_date = date.fromisoformat(report[-1]["date"])
        start_date = date.fromisoformat(report[0]["date"])

        for day in report:
            day_date = date.fromisoformat(day["date"])
            day["label"] = f"{day_date.strftime('%a')} {day_date.day}"

        previous_report = get_weekly_report(
            current_user.user_id,
            start_date - timedelta(days=1)
        )

        if start_date.month == end_date.month:
            range_display = (
                f"{start_date.day} – {end_date.day} "
                f"{end_date.strftime('%B %Y')}"
            )
        else:
            range_display = (
                f"{start_date.day} {start_date.strftime('%b')} – "
                f"{end_date.day} {end_date.strftime('%b %Y')}"
            )

        return render_template(
            "reports/reports.html",
            report=report,
            stats=build_weekly_stats(report, previous_report, profile),
            calorie_goal=profile.daily_calorie_target if profile else 0,
            range_display=range_display,
            today_iso=date.today().isoformat()
        )

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
        bmi=get_bmi_summary(profile),
        today_display=(
            datetime.strptime(today["date"], "%Y-%m-%d").strftime("%A")
            + f", {datetime.strptime(today['date'], '%Y-%m-%d').day} "
            + datetime.strptime(today["date"], "%Y-%m-%d").strftime("%B")
        ),
        calorie_goal=calorie_goal,
        protein_goal=protein_goal,
        carbohydrates_goal=carbohydrates_goal,
        fats_goal=fats_goal,
        week=get_weekly_report(current_user.user_id),
        meals=[
            meal for meal in get_user_meals(current_user.user_id)
            if meal.date.isoformat() == today["date"]
        ]
    )