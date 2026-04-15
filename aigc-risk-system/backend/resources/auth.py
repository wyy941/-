from flask import request
from flask_restful import Resource

from extensions import db
from models.user import User
from services.cache_service import cache_delete_prefix
from utils.auth import generate_token
from utils.response import error, success


def _home_route_by_role(role: str) -> str:
    if role == "student":
        return "/student-center"
    if role == "teacher":
        return "/teacher-center"
    return "/admin-center"


class RegisterResource(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        role = (data.get("role") or "student").strip()

        if not username or not password:
            return error("用户名和密码不能为空", 400)

        existed = User.query.filter_by(username=username).first()
        if existed:
            return error("用户名已存在", 400)

        user = User(
            username=username,
            role=role,
            grade=data.get("grade"),
            major=data.get("major"),
            class_name=data.get("class_name"),
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        cache_delete_prefix("dashboard:overview:")

        return success(user.to_dict(), "注册成功", 201)


class LoginResource(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return error("用户名或密码错误", 401)

        token = generate_token(user)
        return success(
            {
                "token": token,
                "user": user.to_dict(),
                "home_route": _home_route_by_role(user.role),
            },
            "登录成功",
            200,
        )
