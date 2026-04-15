from flask import request
from flask_restful import Resource
from sqlalchemy import or_

from extensions import db
from models.assessment import AssessmentResult
from models.user import User
from services.assessment_query_service import assessment_count_map, latest_assessment_map
from services.cache_service import cache_delete_prefix
from services.teacher_scope_service import (
    scoped_student_query,
    sync_teacher_assignments,
    user_can_access_student,
)
from utils.permissions import require_admin, require_login
from utils.response import error, success

RISK_LEVELS = ("低风险", "中风险", "高风险")
TEXT_FILTER_FIELDS = ("role", "grade", "major", "class_name")
KEYWORD_SEARCH_FIELDS = ("username", "grade", "major", "class_name")
FILTER_CHAIN = ("grade", "major", "class_name", "risk_level")
QUERY_PAGE_SIZE = 12
QUERY_PAGE_SIZE_MAX = 50


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    return None


def _coerce_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value or default)
    except (TypeError, ValueError):
        numeric = default
    return max(minimum, min(maximum, numeric))


def _serialize_history(items: list[AssessmentResult]) -> list[dict]:
    return [
        {
            "assessment_id": item.id,
            "risk_level": item.risk_level,
            "adjusted_score": round(float(item.adjusted_score), 2),
            "total_score": round(float(item.total_score), 2),
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


def _request_filters() -> dict:
    return {
        "keyword": _normalize_text(request.args.get("keyword")) or "",
        "role": _normalize_text(request.args.get("role")) or "",
        "grade": _normalize_text(request.args.get("grade")) or "",
        "major": _normalize_text(request.args.get("major")) or "",
        "class_name": _normalize_text(request.args.get("class_name")) or "",
        "risk_level": _normalize_text(request.args.get("risk_level")) or "",
        "has_assessment": _coerce_bool(request.args.get("has_assessment")),
    }


def _build_user_query(
    filters: dict | None = None,
    include_fields: tuple[str, ...] = TEXT_FILTER_FIELDS,
    base_query=None,
):
    filters = filters or _request_filters()
    query = (base_query or User.query).order_by(User.id.asc())

    for field in include_fields:
        value = _normalize_text(filters.get(field))
        if value:
            query = query.filter(getattr(User, field) == value)

    keyword = _normalize_text(filters.get("keyword"))
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                *[getattr(User, field).ilike(keyword_pattern) for field in KEYWORD_SEARCH_FIELDS]
            )
        )

    return query


def _serialize_users(users: list[User]) -> list[dict]:
    user_ids = [user.id for user in users]
    latest_map = latest_assessment_map(user_ids)
    count_map = assessment_count_map(user_ids)

    payload = []
    for user in users:
        item = user.to_dict()
        item["latest_assessment"] = latest_map.get(user.id)
        item["assessment_count"] = count_map.get(user.id, 0)
        payload.append(item)
    return payload


def _apply_post_filters(
    items: list[dict],
    filters: dict | None = None,
    include_risk_level: bool = True,
    include_has_assessment: bool = True,
) -> list[dict]:
    filters = filters or _request_filters()
    risk_level = _normalize_text(filters.get("risk_level")) if include_risk_level else None
    has_assessment = filters.get("has_assessment") if include_has_assessment else None

    result = items
    if has_assessment is True:
        result = [item for item in result if item.get("latest_assessment")]
    elif has_assessment is False:
        result = [item for item in result if not item.get("latest_assessment")]

    if risk_level:
        result = [
            item
            for item in result
            if item.get("latest_assessment")
            and item["latest_assessment"].get("risk_level") == risk_level
        ]

    return result


def _filter_option_items(items: list[dict], filters: dict, exclude_field: str) -> list[dict]:
    result = items
    for field in TEXT_FILTER_FIELDS:
        if field == exclude_field:
            continue
        value = _normalize_text(filters.get(field))
        if value:
            result = [item for item in result if item.get(field) == value]

    option_filters = dict(filters)
    if exclude_field == "risk_level":
        option_filters["risk_level"] = ""

    return _apply_post_filters(result, option_filters)


def _dynamic_filter_options(items: list[dict], filters: dict) -> dict:
    role_items = _filter_option_items(items, filters, exclude_field="role")
    grade_items = _filter_option_items(items, filters, exclude_field="grade")
    major_items = _filter_option_items(items, filters, exclude_field="major")
    class_items = _filter_option_items(items, filters, exclude_field="class_name")
    risk_items = _filter_option_items(items, filters, exclude_field="risk_level")

    return {
        "roles": sorted({item["role"] for item in role_items if item.get("role")}),
        "grades": sorted({item["grade"] for item in grade_items if item.get("grade")}),
        "majors": sorted({item["major"] for item in major_items if item.get("major")}),
        "classes": (
            sorted({item["class_name"] for item in class_items if item.get("class_name")})
            if filters.get("grade") and filters.get("major")
            else []
        ),
        "risk_levels": (
            sorted(
                {
                    item["latest_assessment"]["risk_level"]
                    for item in risk_items
                    if item.get("latest_assessment")
                    and item["latest_assessment"].get("risk_level")
                },
                key=lambda level: RISK_LEVELS.index(level) if level in RISK_LEVELS else 99,
            )
            if filters.get("grade") and filters.get("major") and filters.get("class_name")
            else []
        ),
        "chain": FILTER_CHAIN,
    }


def _query_summary(items: list[dict]) -> dict:
    assessed = [item for item in items if item.get("latest_assessment")]
    high_risk_count = sum(
        1
        for item in assessed
        if item["latest_assessment"].get("risk_level") == "高风险"
    )
    latest_times = [item["latest_assessment"]["created_at"] for item in assessed]
    avg_score = (
        round(
            sum(float(item["latest_assessment"]["adjusted_score"]) for item in assessed)
            / len(assessed),
            2,
        )
        if assessed
        else 0
    )

    return {
        "total_users": len(items),
        "assessed_users": len(assessed),
        "unassessed_users": len(items) - len(assessed),
        "assessment_record_count": sum(int(item.get("assessment_count") or 0) for item in items),
        "high_risk_count": high_risk_count,
        "average_adjusted_score": avg_score,
        "latest_assessment_at": max(latest_times) if latest_times else None,
    }


def _find_user_for_profile(user_id: str | None, username: str | None) -> User | None:
    normalized_username = _normalize_text(username)

    if user_id:
        try:
            return User.query.get(int(user_id))
        except (TypeError, ValueError):
            return None

    if not normalized_username:
        return None

    return (
        User.query.filter(User.username.ilike(normalized_username))
        .order_by(User.id.asc())
        .first()
    )


def _teacher_assignment_option_query(grade: str | None = None, major: str | None = None):
    query = User.query.filter(User.role == "student")
    if grade:
        query = query.filter(User.grade == grade)
    if major:
        query = query.filter(User.major == major)
    return query


def _teacher_assignment_options(grade: str | None = None, major: str | None = None) -> dict:
    students = _teacher_assignment_option_query(grade, major).all()
    return {
        "grades": sorted({item.grade for item in User.query.filter(User.role == "student").all() if item.grade}),
        "majors": sorted({item.major for item in _teacher_assignment_option_query(grade).all() if item.major}),
        "classes": (
            sorted({item.class_name for item in students if item.class_name})
            if grade and major
            else []
        ),
    }


def _serialize_teacher(user: User) -> dict:
    payload = user.to_dict()
    payload["assignment_count"] = len(payload.get("teacher_assignments") or [])
    return payload


class UserListResource(Resource):
    def get(self):
        current_user, response = require_login()
        if response is not None:
            return response

        filters = _request_filters()
        if current_user.role == "student":
            users = [current_user]
        elif current_user.role == "teacher":
            users = _build_user_query(filters, base_query=scoped_student_query(current_user)).all()
        else:
            users = _build_user_query(filters).all()

        payload = _apply_post_filters(_serialize_users(users), filters)
        return success(payload)


class UserQueryResource(Resource):
    def get(self):
        _, response = require_admin()
        if response is not None:
            return response

        filters = _request_filters()
        page = _coerce_int(request.args.get("page"), default=1, minimum=1, maximum=9999)
        page_size = _coerce_int(
            request.args.get("page_size"),
            default=QUERY_PAGE_SIZE,
            minimum=1,
            maximum=QUERY_PAGE_SIZE_MAX,
        )

        option_source_users = _build_user_query(filters, include_fields=()).all()
        option_source_payload = _serialize_users(option_source_users)

        users = _build_user_query(filters).all()
        payload = _apply_post_filters(_serialize_users(users), filters)
        total = len(payload)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = payload[start:end]
        total_pages = max((total + page_size - 1) // page_size, 1)

        return success(
            {
                "items": page_items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                },
                "summary": _query_summary(payload),
                "filter_options": _dynamic_filter_options(option_source_payload, filters),
                "filters": filters,
            }
        )


class UserProfileResource(Resource):
    def get(self):
        current_user, response = require_login()
        if response is not None:
            return response

        user = _find_user_for_profile(
            request.args.get("user_id"),
            request.args.get("username"),
        )
        if not user:
            return error("未找到对应学生，请输入完整用户名或有效 user_id", 404)

        if not user_can_access_student(current_user, user):
            return error("当前账号无权访问该学生档案", 403)

        assessments = (
            AssessmentResult.query.filter_by(user_id=user.id)
            .order_by(AssessmentResult.created_at.desc(), AssessmentResult.id.desc())
            .all()
        )
        latest_assessment = assessments[0] if assessments else None

        return success(
            {
                "user": user.to_dict(),
                "latest_assessment": (
                    {
                        "assessment_id": latest_assessment.id,
                        "risk_level": latest_assessment.risk_level,
                        "adjusted_score": round(float(latest_assessment.adjusted_score), 2),
                        "total_score": round(float(latest_assessment.total_score), 2),
                        "created_at": latest_assessment.created_at.isoformat(),
                    }
                    if latest_assessment
                    else None
                ),
                "assessment_count": len(assessments),
                "history_preview": _serialize_history(assessments[:6]),
            }
        )


class TeacherListResource(Resource):
    def get(self):
        _, response = require_admin()
        if response is not None:
            return response

        teachers = (
            User.query.filter(User.role == "teacher")
            .order_by(User.id.asc())
            .all()
        )
        return success([_serialize_teacher(item) for item in teachers])


class TeacherAssignmentOptionsResource(Resource):
    def get(self):
        _, response = require_admin()
        if response is not None:
            return response

        grade = _normalize_text(request.args.get("grade"))
        major = _normalize_text(request.args.get("major"))
        return success(_teacher_assignment_options(grade, major))


class TeacherAssignmentResource(Resource):
    def get(self, teacher_id: int):
        _, response = require_admin()
        if response is not None:
            return response

        teacher = User.query.get(teacher_id)
        if not teacher or teacher.role != "teacher":
            return error("未找到对应教师账号", 404)

        return success(_serialize_teacher(teacher))

    def put(self, teacher_id: int):
        _, response = require_admin()
        if response is not None:
            return response

        teacher = User.query.get(teacher_id)
        if not teacher or teacher.role != "teacher":
            return error("未找到对应教师账号", 404)

        data = request.get_json(silent=True) or {}
        assignments = data.get("assignments")
        if assignments is not None and not isinstance(assignments, list):
            return error("assignments 必须是数组", 400)

        sync_teacher_assignments(teacher, assignments or [])
        db.session.commit()
        cache_delete_prefix("dashboard:overview:")

        return success(_serialize_teacher(teacher), "教师任教范围已更新")
