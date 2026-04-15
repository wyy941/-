import json

import pandas as pd
from flask import request
from flask_restful import Resource

from extensions import db
from models.assessment import AssessmentResult
from models.indicator import Indicator
from models.user import User
from services.cache_service import cache_delete_prefix
from services.collaborative_filter import similarity_adjust_score
from services.report_service import build_report
from services.risk_engine import (
    DEFAULT_INDICATORS,
    FEATURE_COLUMNS,
    evaluate_risk,
    fuzzify_score,
    indicator_sort_key,
)
from services.student_questionnaire_service import (
    ANSWER_VALUES,
    QUESTION_LOOKUP,
    STUDENT_QUESTIONNAIRE_QUESTIONS,
    questionnaire_answer_to_indicator_scores,
    student_questionnaire_meta,
)
from services.workflow_service import sync_warning_task_for_user
from utils.permissions import TEACHER_SIDE_ROLES, require_roles, require_self_or_roles
from utils.response import error, success


def _history_dataframe() -> pd.DataFrame:
    rows = []
    records = AssessmentResult.query.order_by(AssessmentResult.created_at.asc()).all()
    for item in records:
        raw_payload = json.loads(item.source_payload_json)
        record = {key: raw_payload.get(key, 0) for key in FEATURE_COLUMNS}
        record["adjusted_score"] = item.adjusted_score
        rows.append(record)
    return pd.DataFrame(rows)


def _enabled_indicator_dicts() -> list[dict]:
    indicators = Indicator.query.filter_by(enabled=True).all()
    if indicators:
        return sorted([item.to_dict() for item in indicators], key=indicator_sort_key)
    return DEFAULT_INDICATORS


def _validate_indicator_payload(
    payload: dict,
    indicator_dicts: list[dict],
    require_all: bool = False,
):
    normalized = {}
    missing = []

    for item in indicator_dicts:
        code = item["code"]
        raw_value = payload.get(code)
        if raw_value in (None, ""):
            if require_all:
                missing.append(item["name"])
                continue
            normalized[code] = 0.0
            continue

        try:
            score = float(raw_value)
        except (TypeError, ValueError):
            return None, error(f"指标“{item['name']}”的分值无效，请按 0-100 分填写。", 400)

        if score < 0 or score > 100:
            return None, error(f"指标“{item['name']}”必须在 0-100 分之间。", 400)

        normalized[code] = round(score, 2)

    if require_all and missing:
        return None, error(
            f"请完成全部指标评分后再提交，未完成项：{', '.join(missing[:5])}",
            400,
        )

    return normalized, None


def _validate_questionnaire_answers(answer_payload: dict):
    if not isinstance(answer_payload, dict):
        return None, error("自我评价提交格式无效。", 400)

    normalized = {}
    missing = []

    for question in STUDENT_QUESTIONNAIRE_QUESTIONS:
        question_id = question["id"]
        raw_value = answer_payload.get(question_id)
        if raw_value in (None, ""):
            missing.append(f"第{question['order']}题")
            continue

        try:
            score = float(raw_value)
        except (TypeError, ValueError):
            return None, error(f"第{question['order']}题的评分无效。", 400)

        if score not in ANSWER_VALUES:
            return None, error(
                f"第{question['order']}题的评分不在允许范围内，请按问卷固定选项作答。",
                400,
            )

        normalized[question_id] = round(score, 2)

    if missing:
        return None, error(
            f"请完成全部 60 道题后再提交，未完成项：{', '.join(missing[:6])}",
            400,
        )

    unknown_ids = sorted(set(answer_payload.keys()) - set(QUESTION_LOOKUP.keys()))
    if unknown_ids:
        return None, error(f"检测到无效题目编号：{', '.join(unknown_ids[:5])}", 400)

    return normalized, None


def _run_assessment(user: User, payload: dict, indicator_dicts: list[dict]):
    history_df = _history_dataframe()
    evaluation = evaluate_risk(payload, indicator_dicts, comparison_df=history_df)
    adjusted_score = similarity_adjust_score(
        history_df,
        evaluation["details"],
        evaluation["total_score"],
    )
    final_level = fuzzify_score(adjusted_score)

    assessment = AssessmentResult(
        user_id=user.id,
        total_score=evaluation["total_score"],
        adjusted_score=adjusted_score,
        risk_level=final_level,
        details_json=json.dumps(evaluation["details"], ensure_ascii=False),
        suggestions_json=json.dumps(evaluation["suggestions"], ensure_ascii=False),
        source_payload_json=json.dumps(
            evaluation["details"],
            ensure_ascii=False,
            sort_keys=True,
        ),
    )

    db.session.add(assessment)
    db.session.commit()
    sync_warning_task_for_user(user.id)
    db.session.commit()
    cache_delete_prefix("dashboard:overview:")

    return assessment, evaluation, adjusted_score, final_level


def _build_teacher_assessment_response(
    user: User,
    assessment: AssessmentResult,
    evaluation: dict,
    adjusted_score: float,
    final_level: str,
    indicator_dicts: list[dict],
) -> dict:
    report = build_report(
        username=user.username,
        total_score=evaluation["total_score"],
        adjusted_score=adjusted_score,
        risk_level=final_level,
        details=evaluation["details"],
        suggestions=evaluation["suggestions"],
        indicator_meta=indicator_dicts,
        profile=user.to_dict(),
        source_payload=evaluation["details"],
        memberships=evaluation["memberships"],
        dimension_breakdown=evaluation["dimension_breakdown"],
        top_risks=evaluation["top_risks"],
        model_details=evaluation["model_details"],
    )

    return {
        "assessment_id": assessment.id,
        "total_score": evaluation["total_score"],
        "adjusted_score": adjusted_score,
        "risk_level": final_level,
        "details": evaluation["details"],
        "suggestions": evaluation["suggestions"],
        "memberships": evaluation["memberships"],
        "confidence": evaluation["confidence"],
        "dimension_breakdown": evaluation["dimension_breakdown"],
        "top_risks": evaluation["top_risks"],
        "model_details": evaluation["model_details"],
        "indicator_meta": evaluation["indicator_meta"],
        "user": user.to_dict(),
        "report": report,
    }


def _student_summary(assessment: AssessmentResult | None) -> dict | None:
    if not assessment:
        return None

    return {
        "assessment_id": assessment.id,
        "final_score": round(float(assessment.adjusted_score), 2),
        "created_at": assessment.created_at.isoformat(),
    }


def _student_overview_payload(user: User) -> dict:
    assessments = (
        AssessmentResult.query.filter_by(user_id=user.id)
        .order_by(AssessmentResult.created_at.asc(), AssessmentResult.id.asc())
        .all()
    )
    latest_assessment = assessments[-1] if assessments else None
    recent_records = list(reversed(assessments[-8:]))

    return {
        "user": user.to_dict(),
        "latest_assessment": _student_summary(latest_assessment),
        "assessment_count": len(assessments),
        "recent_records": [
            {
                "assessment_id": item.id,
                "final_score": round(float(item.adjusted_score), 2),
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_records
        ],
        "trend": [
            {
                "assessment_id": item.id,
                "date": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "final_score": round(float(item.adjusted_score), 2),
            }
            for item in assessments
        ],
    }


class EvaluateAssessmentResource(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}

        user_id = data.get("user_id")
        if not user_id:
            return error("user_id 不能为空")

        _, response = require_self_or_roles(user_id, *TEACHER_SIDE_ROLES)
        if response is not None:
            return response

        user = User.query.get(user_id)
        if not user:
            return error("用户不存在", 404)

        indicator_dicts = _enabled_indicator_dicts()
        payload, response = _validate_indicator_payload(data.get("payload") or {}, indicator_dicts)
        if response is not None:
            return response

        assessment, evaluation, adjusted_score, final_level = _run_assessment(
            user,
            payload,
            indicator_dicts,
        )
        return success(
            _build_teacher_assessment_response(
                user,
                assessment,
                evaluation,
                adjusted_score,
                final_level,
                indicator_dicts,
            ),
            "评估成功",
            201,
        )


class StudentSelfAssessmentMetaResource(Resource):
    def get(self):
        _, response = require_roles("student")
        if response is not None:
            return response

        return success(student_questionnaire_meta())


class StudentSelfAssessmentResource(Resource):
    def get(self):
        current_user, response = require_roles("student")
        if response is not None:
            return response

        return success(_student_overview_payload(current_user))

    def post(self):
        current_user, response = require_roles("student")
        if response is not None:
            return response

        answers, response = _validate_questionnaire_answers(
            (request.get_json(silent=True) or {}).get("answers") or {}
        )
        if response is not None:
            return response

        indicator_dicts = _enabled_indicator_dicts()
        indicator_scores = questionnaire_answer_to_indicator_scores(answers)
        assessment, _, _, _ = _run_assessment(current_user, indicator_scores, indicator_dicts)

        return success(
            {
                "assessment": _student_summary(assessment),
                "assessment_count": AssessmentResult.query.filter_by(user_id=current_user.id).count(),
            },
            "自我评价提交成功",
            201,
        )


class AssessmentHistoryResource(Resource):
    def get(self, user_id: int):
        current_user, response = require_self_or_roles(user_id, *TEACHER_SIDE_ROLES)
        if response is not None:
            return response

        results = (
            AssessmentResult.query.filter_by(user_id=user_id)
            .order_by(AssessmentResult.created_at.asc())
            .all()
        )
        is_student_self = current_user.role == "student" and current_user.id == int(user_id)

        payload = []
        for item in results:
            if is_student_self:
                payload.append(
                    {
                        "id": item.id,
                        "final_score": round(float(item.adjusted_score), 2),
                        "created_at": item.created_at.isoformat(),
                    }
                )
                continue

            payload.append(
                {
                    "id": item.id,
                    "total_score": item.total_score,
                    "adjusted_score": item.adjusted_score,
                    "risk_level": item.risk_level,
                    "created_at": item.created_at.isoformat(),
                    "details": json.loads(item.details_json),
                    "suggestions": json.loads(item.suggestions_json),
                }
            )

        return success(payload)
