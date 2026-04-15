import json

import pandas as pd
from flask import make_response
from flask_restful import Resource

from models.assessment import AssessmentResult
from models.indicator import Indicator
from services.report_service import build_report
from services.risk_engine import DEFAULT_INDICATORS, FEATURE_COLUMNS, evaluate_risk
from utils.permissions import TEACHER_SIDE_ROLES, require_self_or_roles
from utils.response import error, success


def _indicator_meta() -> dict:
    meta = {item["code"]: item for item in DEFAULT_INDICATORS}
    for item in Indicator.query.all():
        meta[item.code] = item.to_dict()
    return meta


def _comparison_frame() -> pd.DataFrame:
    rows = []
    records = AssessmentResult.query.order_by(AssessmentResult.created_at.asc()).all()
    for item in records:
        raw_payload = json.loads(item.source_payload_json)
        rows.append({key: raw_payload.get(key, 0) for key in FEATURE_COLUMNS})
    return pd.DataFrame(rows)


def _report_from_assessment(assessment: AssessmentResult) -> dict:
    details = json.loads(assessment.details_json)
    indicator_meta = _indicator_meta()
    evaluation = evaluate_risk(
        details,
        indicator_meta.values(),
        comparison_df=_comparison_frame(),
    )
    return build_report(
        username=assessment.user.username if assessment.user else f"user_{assessment.user_id}",
        total_score=assessment.total_score,
        adjusted_score=assessment.adjusted_score,
        risk_level=assessment.risk_level,
        details=details,
        suggestions=json.loads(assessment.suggestions_json),
        indicator_meta=indicator_meta,
        profile=assessment.user.to_dict() if assessment.user else {},
        source_payload=json.loads(assessment.source_payload_json),
        assessment_id=assessment.id,
        created_at=assessment.created_at.isoformat(),
        memberships=evaluation["memberships"],
        dimension_breakdown=evaluation["dimension_breakdown"],
        top_risks=evaluation["top_risks"],
        model_details=evaluation["model_details"],
    )


class LatestReportResource(Resource):
    def get(self, user_id: int):
        current_user, response = require_self_or_roles(user_id, *TEACHER_SIDE_ROLES)
        if response is not None:
            return response
        if current_user.role == "student":
            return error("学生端不提供详细报告，请在自我评价页面查看总分结果。", 403)

        assessment = (
            AssessmentResult.query.filter_by(user_id=user_id)
            .order_by(AssessmentResult.created_at.desc())
            .first()
        )
        if not assessment:
            return error("该用户暂无评估报告", 404)

        return success(_report_from_assessment(assessment))


class AssessmentReportResource(Resource):
    def get(self, assessment_id: int):
        assessment = AssessmentResult.query.get(assessment_id)
        if not assessment:
            return error("评估记录不存在", 404)

        current_user, response = require_self_or_roles(assessment.user_id, *TEACHER_SIDE_ROLES)
        if response is not None:
            return response
        if current_user.role == "student":
            return error("学生端不提供详细报告，请在自我评价页面查看总分结果。", 403)

        return success(_report_from_assessment(assessment))


class AssessmentReportExportResource(Resource):
    def get(self, assessment_id: int):
        assessment = AssessmentResult.query.get(assessment_id)
        if not assessment:
            return error("评估记录不存在", 404)

        current_user, response = require_self_or_roles(assessment.user_id, *TEACHER_SIDE_ROLES)
        if response is not None:
            return response
        if current_user.role == "student":
            return error("学生端不提供详细报告导出。", 403)

        report = _report_from_assessment(assessment)
        response = make_response(json.dumps(report, ensure_ascii=False, indent=2))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f'attachment; filename="aigc-risk-report-{assessment_id}.json"'
        )
        return response
