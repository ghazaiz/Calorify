from datetime import date, datetime

from app.core.extensions import db


class Meal(db.Model):
    __tablename__ = "meals"

    meal_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    food_name = db.Column(db.String(200), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)

    quantity = db.Column(db.Float, nullable=False)
    serving_unit = db.Column(db.String(50), nullable=False)

    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbohydrates = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)

    date = db.Column(db.Date, default=date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)