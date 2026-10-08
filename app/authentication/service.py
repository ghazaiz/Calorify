from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.core.extensions import db
from app.profile.models import User


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def register_user(username, email, password):
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return None

    password_hash = hash_password(password)

    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        created_at=datetime.utcnow()
    )

    db.session.add(user)
    db.session.commit()

    return user


def login_user(email, password):
    user = User.query.filter_by(email=email).first()

    if user and verify_password(password, user.password_hash):
        return user

    return None
print("Hello")