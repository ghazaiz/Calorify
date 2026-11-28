
from datetime import datetime
from flask_login import UserMixin
from app.core.extensions import db
from app.profile.targets import calculate_daily_calorie_target, calculate_macro_targets


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False
    )

    def get_id(self):
        return str(self.user_id)

class Profile(db.Model):
    __tablename__ = "profiles"

    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        unique=True,
        nullable=False
    )

    age = db.Column(db.Integer)
    sex = db.Column(db.String(20))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    activity_level = db.Column(db.String(50))
    goal = db.Column(db.String(50))
    weekly_loss = db.Column(db.Float)

    @property
    def daily_calorie_target(self):
        inputs = (self.age, self.sex, self.height_cm, self.weight_kg, self.activity_level, self.goal)
        if any(value is None for value in inputs):
            return None
        return calculate_daily_calorie_target(*inputs, weekly_loss=self.weekly_loss)

    def _macro_targets(self):
        calories = self.daily_calorie_target
        return calculate_macro_targets(calories) if calories is not None else (None, None, None)

    @property
    def protein_target(self):
        return self._macro_targets()[0]

    @property
    def carbohydrates_target(self):
        return self._macro_targets()[1]

    @property
    def fats_target(self):
        return self._macro_targets()[2]
