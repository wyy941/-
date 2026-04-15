import json

from sqlalchemy import func

from extensions import db
from models.assessment import AssessmentResult
from services.risk_engine import DIMENSION_LABELS, FEATURE_DIMENSIONS


def _top_dimension_name(assessment: AssessmentResult | None) -> str:
    if assessment is None:
        return "未评估"

    details = json.loads(assessment.details_json or "{}")
    dimension_scores: dict[str, list[float]] = {}
    for code, score in details.items():
        dimension = FEATURE_DIMENSIONS.get(code, "custom")
        dimension_scores.setdefault(dimension, []).append(float(score))

    if not dimension_scores:
        return "未识别"

    ranked = sorted(
        (
            (dimension, sum(scores) / max(len(scores), 1))
            for dimension, scores in dimension_scores.items()
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return DIMENSION_LABELS.get(ranked[0][0], ranked[0][0])


def latest_assessment_record_map(user_ids: list[int]) -> dict[int, AssessmentResult]:
    if not user_ids:
        return {}

    rows = (
        AssessmentResult.query.filter(AssessmentResult.user_id.in_(user_ids))
        .order_by(
            AssessmentResult.user_id.asc(),
            AssessmentResult.created_at.desc(),
            AssessmentResult.id.desc(),
        )
        .all()
    )

    mapping: dict[int, AssessmentResult] = {}
    for row in rows:
        if row.user_id not in mapping:
            mapping[row.user_id] = row
    return mapping


def serialize_assessment_snapshot(
    assessment: AssessmentResult | None,
    include_top_dimension: bool = False,
) -> dict | None:
    if assessment is None:
        return None

    payload = {
        "assessment_id": assessment.id,
        "risk_level": assessment.risk_level,
        "adjusted_score": round(float(assessment.adjusted_score), 2),
        "total_score": round(float(assessment.total_score), 2),
        "created_at": assessment.created_at.isoformat(),
    }
    if include_top_dimension:
        payload["top_dimension"] = _top_dimension_name(assessment)
    return payload


def latest_assessment_map(
    user_ids: list[int],
    include_top_dimension: bool = False,
) -> dict[int, dict]:
    return {
        user_id: serialize_assessment_snapshot(record, include_top_dimension)
        for user_id, record in latest_assessment_record_map(user_ids).items()
    }


def assessment_count_map(user_ids: list[int]) -> dict[int, int]:
    if not user_ids:
        return {}

    rows = (
        db.session.query(
            AssessmentResult.user_id,
            func.count(AssessmentResult.id),
        )
        .filter(AssessmentResult.user_id.in_(user_ids))
        .group_by(AssessmentResult.user_id)
        .all()
    )
    return {int(user_id): int(count) for user_id, count in rows}
