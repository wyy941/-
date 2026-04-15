from flask import request
from flask_restful import Resource

from extensions import db
from models.indicator import Indicator
from services.risk_engine import indicator_sort_key
from utils.permissions import require_admin, require_teacher_side
from utils.response import error, success


class IndicatorListResource(Resource):
    def get(self):
        _, response = require_teacher_side()
        if response is not None:
            return response

        indicators = sorted(
            [item.to_dict() for item in Indicator.query.all()],
            key=indicator_sort_key,
        )
        return success(indicators)

    def post(self):
        _, response = require_admin()
        if response is not None:
            return response

        data = request.get_json(silent=True) or {}
        code = (data.get("code") or "").strip()
        name = (data.get("name") or "").strip()

        if not code or not name:
            return error("指标编码和指标名称不能为空")

        existed = Indicator.query.filter_by(code=code).first()
        if existed:
            return error("指标编码已存在")

        indicator = Indicator(
            code=code,
            name=name,
            weight=float(data.get("weight", 0)),
            description=data.get("description"),
            score_standard=data.get("score_standard"),
            enabled=bool(data.get("enabled", True)),
        )
        db.session.add(indicator)
        db.session.commit()
        return success(indicator.to_dict(), "新增指标成功", 201)


class IndicatorResource(Resource):
    def put(self, indicator_id: int):
        _, response = require_admin()
        if response is not None:
            return response

        indicator = Indicator.query.get(indicator_id)
        if not indicator:
            return error("指标不存在", 404)

        data = request.get_json(silent=True) or {}
        indicator.code = data.get("code", indicator.code)
        indicator.name = data.get("name", indicator.name)
        indicator.weight = float(data.get("weight", indicator.weight))
        indicator.description = data.get("description", indicator.description)
        indicator.score_standard = data.get("score_standard", indicator.score_standard)
        indicator.enabled = bool(data.get("enabled", indicator.enabled))

        db.session.commit()
        return success(indicator.to_dict(), "更新成功")

    def delete(self, indicator_id: int):
        _, response = require_admin()
        if response is not None:
            return response

        indicator = Indicator.query.get(indicator_id)
        if not indicator:
            return error("指标不存在", 404)

        db.session.delete(indicator)
        db.session.commit()
        return success(None, "删除成功")
