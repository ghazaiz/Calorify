from flask_login import UserMixin
from app.core.extensions import db
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
    db.DateTime,
    default=datetime.utcnow,
    nullable=False
)

    profile = db.relationship(
    "Profile",
    backref="user",
    uselist=False
)
    meals = db.relationship(
    "Meal",
    backref="user",
    lazy=True
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
    daily_calorie_target = db.Column(db.Integer)
    protein_target = db.Column(db.Float)
    carbohydrates_target = db.Column(db.Float)
    fats_target = db.Column(db.Float)