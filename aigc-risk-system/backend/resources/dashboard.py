import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from flask import request
from flask_restful import Resource

from models.assessment import AssessmentResult
from models.user import User
from services.assessment_query_service import latest_assessment_record_map
from services.cache_service import cache_get_json, cache_set_json
from services.risk_engine import DIMENSION_LABELS, FEATURE_DIMENSIONS, FEATURE_LABELS
from services.teacher_scope_service import scoped_student_query, teacher_scope_signature
from utils.permissions import TEACHER_SIDE_ROLES, require_roles, require_self_or_roles
from utils.response import success

FILTER_KEYS = ("role", "grade", "major", "class_name", "risk_level")
RISK_LEVELS = ("低风险", "中风险", "高风险")
SCORE_BANDS = (
    ("0-39", 0, 40),
    ("40-54", 40, 55),
    ("55-69", 55, 70),
    ("70-100", 70, 101),
)
UNKNOWN_LABEL = "未分组"


def _extract_filters() -> dict:
    return {
        key: value.strip()
        for key in FILTER_KEYS
        if (value := request.args.get(key))
    }


def _base_student_query(current_user):
    if current_user.role == "teacher":
        return scoped_student_query(current_user)
    return User.query.filter(User.role == "student")


def _apply_student_filters(query, filters: dict):
    for field in ("grade", "major", "class_name"):
        if filters.get(field):
            query = query.filter(getattr(User, field) == filters[field])
    return query


def _details_for(record: AssessmentResult | None) -> dict:
    if record is None:
        return {}
    try:
        return json.loads(record.details_json or "{}")
    except (TypeError, ValueError):
        return {}


def _score_band(score: float) -> str:
    numeric_score = float(score or 0)
    for label, lower, upper in SCORE_BANDS:
        if lower <= numeric_score < upper:
            return label
    return SCORE_BANDS[-1][0]


def _dimension_profile(details: dict) -> dict:
    sums = defaultdict(float)
    counts = defaultdict(int)

    for key, value in details.items():
        dimension = FEATURE_DIMENSIONS.get(key, "custom")
        sums[dimension] += float(value)
        counts[dimension] += 1

    return {
        dimension: round(sums[dimension] / max(counts[dimension], 1), 2)
        for dimension in sums
    }


def _top_dimension_name(details: dict) -> str:
    profile = _dimension_profile(details)
    if not profile:
        return "未识别"
    dimension = max(profile, key=profile.get)
    return DIMENSION_LABELS.get(dimension, dimension)


def _risk_options(users: list[User], filters: dict) -> list[str]:
    if not (filters.get("grade") and filters.get("major") and filters.get("class_name")):
        return []

    filtered_users = users
    if filters.get("grade"):
        filtered_users = [item for item in filtered_users if item.grade == filters["grade"]]
    if filters.get("major"):
        filtered_users = [item for item in filtered_users if item.major == filters["major"]]
    if filters.get("class_name"):
        filtered_users = [item for item in filtered_users if item.class_name == filters["class_name"]]

    latest_map = latest_assessment_record_map([item.id for item in filtered_users])
    levels = {record.risk_level for record in latest_map.values() if record.risk_level}
    return sorted(levels, key=lambda level: RISK_LEVELS.index(level) if level in RISK_LEVELS else 99)


def _filter_options(filters: dict | None = None, current_user=None) -> dict:
    filters = filters or {}
    users = _base_student_query(current_user).all() if current_user else []

    grade_users = users
    major_users = users
    if filters.get("grade"):
        major_users = [item for item in major_users if item.grade == filters["grade"]]

    class_users = (
        [
            item
            for item in users
            if item.grade == filters.get("grade") and item.major == filters.get("major")
        ]
        if filters.get("grade") and filters.get("major")
        else []
    )

    return {
        "roles": ["student"],
        "grades": sorted({item.grade for item in grade_users if item.grade}),
        "majors": sorted({item.major for item in major_users if item.major}),
        "classes": sorted({item.class_name for item in class_users if item.class_name}),
        "risk_levels": _risk_options(users, filters),
    }


def _empty_overview(filters: dict, current_user=None) -> dict:
    return {
        "filters": filters,
        "total_users": 0,
        "total_assessments": 0,
        "latest_assessed_user_count": 0,
        "average_adjusted_score": 0,
        "alert_user_count": 0,
        "recent_assessment_count": 0,
        "risk_distribution": {level: 0 for level in RISK_LEVELS},
        "score_band_distribution": {label: 0 for label, _, _ in SCORE_BANDS},
        "indicator_average": {},
        "indicator_ranking": [],
        "dimension_average": {},
        "risk_by_grade": [],
        "major_risk_stats": [],
        "class_risk_ranking": [],
        "user_role_distribution": {"student": 0},
        "trend_points": [],
        "monthly_risk_trend": [],
        "high_risk_users": [],
        "recent_alerts": [],
        "filter_options": _filter_options(filters, current_user),
    }


def _grade_payload(grade_stats: dict) -> list[dict]:
    rows = []
    for grade in sorted(grade_stats.keys()):
        item = grade_stats[grade]
        total = item["count"]
        rows.append(
            {
                "grade": grade,
                "低风险": item["levels"]["低风险"],
                "中风险": item["levels"]["中风险"],
                "高风险": item["levels"]["高风险"],
                "total": total,
                "avg_score": round(item["score_sum"] / max(total, 1), 2),
            }
        )
    return rows


def _monthly_payload(monthly_stats: dict) -> list[dict]:
    rows = []
    for month in sorted(monthly_stats.keys()):
        levels = monthly_stats[month]
        rows.append(
            {
                "month": month,
                "低风险": levels["低风险"],
                "中风险": levels["中风险"],
                "高风险": levels["高风险"],
                "total": sum(levels[level] for level in RISK_LEVELS),
            }
        )
    return rows


def _major_payload(major_stats: dict) -> list[dict]:
    rows = []
    for major, item in major_stats.items():
        total = item["latest_count"] or 1
        rows.append(
            {
                "major": major,
                "assessment_count": item["history_count"],
                "student_count": len(item["users"]),
                "avg_score": round(item["score_sum"] / total, 2),
                "high_risk_rate": round(item["high_risk"] * 100 / total, 1),
                "medium_risk_rate": round(item["medium_risk"] * 100 / total, 1),
            }
        )
    rows.sort(key=lambda item: (item["avg_score"], item["assessment_count"]), reverse=True)
    return rows[:8]


def _class_payload(class_stats: dict) -> list[dict]:
    rows = []
    for class_name, item in class_stats.items():
        total = item["latest_count"] or 1
        rows.append(
            {
                "class_name": class_name,
                "assessment_count": item["history_count"],
                "student_count": len(item["users"]),
                "avg_score": round(item["score_sum"] / total, 2),
                "high_risk_rate": round(item["high_risk"] * 100 / total, 1),
            }
        )
    rows.sort(key=lambda item: (item["avg_score"], item["high_risk_rate"]), reverse=True)
    return rows[:8]


class OverviewDashboardResource(Resource):
    def get(self):
        current_user, response = require_roles(*TEACHER_SIDE_ROLES)
        if response is not None:
            return response

        filters = _extract_filters()
        cache_key = (
            "dashboard:overview:"
            f"{teacher_scope_signature(current_user)}:"
            f"{json.dumps(filters, ensure_ascii=False, sort_keys=True)}"
        )
        cached = cache_get_json(cache_key)
        if cached is not None:
            return success(cached)

        users = _apply_student_filters(_base_student_query(current_user), filters).all()
        if not users:
            payload = _empty_overview(filters, current_user)
            cache_set_json(cache_key, payload)
            return success(payload)

        filtered_user_ids = [item.id for item in users]
        latest_record_map = latest_assessment_record_map(filtered_user_ids)
        latest_records = list(latest_record_map.values())

        if filters.get("risk_level"):
            latest_records = [
                item for item in latest_records if item.risk_level == filters["risk_level"]
            ]
            matched_user_ids = {item.user_id for item in latest_records}
            users = [item for item in users if item.id in matched_user_ids]
            filtered_user_ids = [item.id for item in users]

        results = (
            AssessmentResult.query.filter(AssessmentResult.user_id.in_(filtered_user_ids))
            .order_by(AssessmentResult.created_at.asc(), AssessmentResult.id.asc())
            .all()
            if filtered_user_ids
            else []
        )

        if not latest_records:
            payload = _empty_overview(filters, current_user)
            payload["total_users"] = len(users)
            payload["total_assessments"] = len(results)
            payload["user_role_distribution"] = {"student": len(users)}
            payload["filter_options"] = _filter_options(filters, current_user)
            cache_set_json(cache_key, payload)
            return success(payload)

        now = datetime.now()
        level_counter = Counter({level: 0 for level in RISK_LEVELS})
        score_band_counter = Counter({label: 0 for label, _, _ in SCORE_BANDS})
        indicator_sums = defaultdict(float)
        dimension_sums = defaultdict(float)
        dimension_counts = defaultdict(int)
        trend_counter = Counter()
        monthly_stats = defaultdict(lambda: Counter({level: 0 for level in RISK_LEVELS}))
        grade_stats = defaultdict(
            lambda: {
                "levels": Counter({level: 0 for level in RISK_LEVELS}),
                "score_sum": 0.0,
                "count": 0,
            }
        )
        major_stats = defaultdict(
            lambda: {
                "score_sum": 0.0,
                "history_count": 0,
                "latest_count": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "users": set(),
            }
        )
        class_stats = defaultdict(
            lambda: {
                "score_sum": 0.0,
                "history_count": 0,
                "latest_count": 0,
                "high_risk": 0,
                "users": set(),
            }
        )

        recent_assessment_count = 0
        for record in results:
            if record.created_at >= now - timedelta(days=30):
                recent_assessment_count += 1

            trend_counter[record.created_at.strftime("%Y-%m-%d")] += 1
            monthly_stats[record.created_at.strftime("%Y-%m")][record.risk_level] += 1

            user = record.user
            major = user.major if user and user.major else UNKNOWN_LABEL
            class_name = user.class_name if user and user.class_name else UNKNOWN_LABEL
            major_stats[major]["history_count"] += 1
            class_stats[class_name]["history_count"] += 1

        adjusted_score_sum = 0.0
        for record in latest_records:
            user = record.user
            grade = user.grade if user and user.grade else UNKNOWN_LABEL
            major = user.major if user and user.major else UNKNOWN_LABEL
            class_name = user.class_name if user and user.class_name else UNKNOWN_LABEL
            adjusted_score = float(record.adjusted_score)
            details = _details_for(record)

            level_counter[record.risk_level] += 1
            score_band_counter[_score_band(adjusted_score)] += 1
            adjusted_score_sum += adjusted_score

            grade_stats[grade]["levels"][record.risk_level] += 1
            grade_stats[grade]["score_sum"] += adjusted_score
            grade_stats[grade]["count"] += 1

            major_stats[major]["score_sum"] += adjusted_score
            major_stats[major]["latest_count"] += 1
            major_stats[major]["users"].add(record.user_id)
            if record.risk_level == "高风险":
                major_stats[major]["high_risk"] += 1
            elif record.risk_level == "中风险":
                major_stats[major]["medium_risk"] += 1

            class_stats[class_name]["score_sum"] += adjusted_score
            class_stats[class_name]["latest_count"] += 1
            class_stats[class_name]["users"].add(record.user_id)
            if record.risk_level == "高风险":
                class_stats[class_name]["high_risk"] += 1

            for key, value in details.items():
                numeric_value = float(value)
                indicator_sums[key] += numeric_value
                dimension = FEATURE_DIMENSIONS.get(key, "custom")
                dimension_sums[dimension] += numeric_value
                dimension_counts[dimension] += 1

        latest_assessed_user_count = len(latest_records)
        indicator_average = {
            FEATURE_LABELS.get(key, key): round(value / max(latest_assessed_user_count, 1), 2)
            for key, value in indicator_sums.items()
        }
        dimension_average = {
            DIMENSION_LABELS.get(key, key): round(
                dimension_sums[key] / max(dimension_counts[key], 1),
                2,
            )
            for key in dimension_sums
        }
        indicator_ranking = sorted(
            [
                {
                    "code": key,
                    "name": FEATURE_LABELS.get(key, key),
                    "average_score": round(value / max(latest_assessed_user_count, 1), 2),
                    "dimension": FEATURE_DIMENSIONS.get(key, "custom"),
                    "dimension_name": DIMENSION_LABELS.get(
                        FEATURE_DIMENSIONS.get(key, "custom"),
                        "自定义指标",
                    ),
                }
                for key, value in indicator_sums.items()
            ],
            key=lambda item: item["average_score"],
            reverse=True,
        )

        ranked_latest = sorted(
            latest_records,
            key=lambda current: (
                current.risk_level == "高风险",
                current.risk_level == "中风险",
                float(current.adjusted_score),
                current.created_at.timestamp(),
            ),
            reverse=True,
        )

        high_risk_users = [
            {
                "user_id": item.user_id,
                "username": item.user.username if item.user else f"user_{item.user_id}",
                "risk_level": item.risk_level,
                "adjusted_score": round(float(item.adjusted_score), 2),
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for item in ranked_latest[:5]
        ]

        recent_alerts = [
            {
                "user_id": item.user_id,
                "username": item.user.username if item.user else f"user_{item.user_id}",
                "grade": item.user.grade if item.user else "",
                "major": item.user.major if item.user else "",
                "class_name": item.user.class_name if item.user else "",
                "risk_level": item.risk_level,
                "adjusted_score": round(float(item.adjusted_score), 2),
                "top_dimension": _top_dimension_name(_details_for(item)),
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for item in ranked_latest[:8]
        ]

        trend_points = [
            {"date": key, "count": trend_counter[key]}
            for key in sorted(trend_counter.keys())
        ]

        payload = {
            "filters": filters,
            "total_users": len(users),
            "total_assessments": len(results),
            "latest_assessed_user_count": latest_assessed_user_count,
            "average_adjusted_score": round(
                adjusted_score_sum / max(latest_assessed_user_count, 1),
                2,
            ),
            "alert_user_count": sum(1 for item in latest_records if item.risk_level == "高风险"),
            "recent_assessment_count": recent_assessment_count,
            "risk_distribution": {level: level_counter[level] for level in RISK_LEVELS},
            "score_band_distribution": {
                label: score_band_counter[label]
                for label, _, _ in SCORE_BANDS
            },
            "indicator_average": indicator_average,
            "indicator_ranking": indicator_ranking[:10],
            "dimension_average": dimension_average,
            "risk_by_grade": _grade_payload(grade_stats),
            "major_risk_stats": _major_payload(major_stats),
            "class_risk_ranking": _class_payload(class_stats),
            "user_role_distribution": {"student": len(users)},
            "trend_points": trend_points,
            "monthly_risk_trend": _monthly_payload(monthly_stats),
            "high_risk_users": high_risk_users,
            "recent_alerts": recent_alerts,
            "filter_options": _filter_options(filters, current_user),
        }
        cache_set_json(cache_key, payload)
        return success(payload)


class UserTrendResource(Resource):
    def get(self, user_id: int):
        _, response = require_self_or_roles(user_id, *TEACHER_SIDE_ROLES)
        if response is not None:
            return response

        results = (
            AssessmentResult.query.filter_by(user_id=user_id)
            .order_by(AssessmentResult.created_at.asc(), AssessmentResult.id.asc())
            .all()
        )

        trend = [
            {
                "assessment_id": item.id,
                "date": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "total_score": item.total_score,
                "adjusted_score": item.adjusted_score,
                "risk_level": item.risk_level,
            }
            for item in results
        ]
        return success(trend)
