from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from flask import current_app

from models.user import User


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_token(user: User) -> str:
    return _serializer().dumps({"user_id": user.id, "username": user.username})


def parse_token(token: str, max_age: int = 60 * 60 * 24) -> Optional[dict]:
    try:
        return _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
