from __future__ import annotations

from typing import Optional

from flask import request

from models.user import User
from services.teacher_scope_service import user_can_access_student
from utils.auth import parse_token
from utils.response import error

ADMIN_ROLES = ("admin",)
TEACHER_SIDE_ROLES = ("teacher", "admin")


def get_current_user() -> Optional[User]:
    authorization = (request.headers.get("Authorization") or "").strip()
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    payload = parse_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    return User.query.get(user_id)


def require_login():
    current_user = get_current_user()
    if current_user is None:
        return None, error("请先登录后再访问该功能", 401)
    return current_user, None


def require_roles(*roles: str):
    current_user, response = require_login()
    if response is not None:
        return None, response

    if roles and current_user.role not in roles:
        return None, error("当前账号无权访问该功能", 403)

    return current_user, None


def require_admin():
    return require_roles(*ADMIN_ROLES)


def require_teacher_side():
    return require_roles(*TEACHER_SIDE_ROLES)


def require_self_or_roles(target_user_id: int | None, *roles: str):
    current_user, response = require_login()
    if response is not None:
        return None, response

    if target_user_id is not None and current_user.id == int(target_user_id):
        return current_user, None

    if roles and current_user.role in roles:
        if current_user.role == "teacher":
            target_user = User.query.get(int(target_user_id)) if target_user_id is not None else None
            if target_user is None or not user_can_access_student(current_user, target_user):
                return None, error("当前账号无权访问该数据", 403)
        return current_user, None

    return None, error("当前账号无权访问该数据", 403)
