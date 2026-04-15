from datetime import datetime

from flask import request
from flask_restful import Resource
from sqlalchemy import or_

from extensions import db
from models.user import User
from models.workflow import InterventionRecord, StudentArchive, WarningTask
from services.assessment_query_service import latest_assessment_map
from services.teacher_scope_service import (
    scoped_student_ids,
    scoped_student_query,
    user_can_access_student,
)
from services.workflow_service import (
    TASK_STATUSES,
    WARNING_LEVELS,
    bootstrap_workflow_demo_data,
    ensure_student_archive_for_user,
)
from utils.permissions import require_teacher_side
from utils.response import error, success

TASK_STATUS_PRIORITY = {status: index for index, status in enumerate(TASK_STATUSES)}
WARNING_LEVEL_PRIORITY = {level: index for index, level in enumerate(WARNING_LEVELS)}


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _coerce_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value or default)
    except (TypeError, ValueError):
        numeric = default
    return max(minimum, min(maximum, numeric))


def _parse_datetime(value: str | None) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    text = text.replace("T", " ")
    try:
        return datetime.fromisoformat(text[:19])
    except ValueError:
        return None


def _request_filters() -> dict:
    return {
        "keyword": _normalize_text(request.args.get("keyword")) or "",
        "grade": _normalize_text(request.args.get("grade")) or "",
        "major": _normalize_text(request.args.get("major")) or "",
        "warning_level": _normalize_text(request.args.get("warning_level")) or "",
        "task_status": _normalize_text(request.args.get("task_status")) or "",
    }


def _base_student_query(filters: dict, current_user):
    query = scoped_student_query(current_user)

    if filters.get("grade"):
        query = query.filter(User.grade == filters["grade"])
    if filters.get("major"):
        query = query.filter(User.major == filters["major"])
    if filters.get("keyword"):
        pattern = f"%{filters['keyword']}%"
        query = query.filter(
            or_(
                User.username.ilike(pattern),
                User.grade.ilike(pattern),
                User.major.ilike(pattern),
                User.class_name.ilike(pattern),
            )
        )

    return query.order_by(User.id.asc())


def _archive_map(user_ids: list[int]) -> dict[int, dict]:
    if not user_ids:
        return {}
    rows = StudentArchive.query.filter(StudentArchive.user_id.in_(user_ids)).all()
    return {row.user_id: row.to_dict() for row in rows}


def _task_maps(user_ids: list[int]) -> tuple[dict[int, dict], dict[int, list[WarningTask]]]:
    if not user_ids:
        return {}, {}

    rows = (
        WarningTask.query.filter(WarningTask.user_id.in_(user_ids))
        .order_by(WarningTask.updated_at.desc(), WarningTask.id.desc())
        .all()
    )
    task_ids = [row.id for row in rows]
    intervention_counts: dict[int, int] = {}
    if task_ids:
        for record in InterventionRecord.query.filter(InterventionRecord.task_id.in_(task_ids)).all():
            intervention_counts[record.task_id] = intervention_counts.get(record.task_id, 0) + 1

    grouped: dict[int, list[WarningTask]] = {}
    for row in rows:
        grouped.setdefault(row.user_id, []).append(row)

    current_map = {}
    for user_id, user_tasks in grouped.items():
        ordered = sorted(
            user_tasks,
            key=lambda item: (
                TASK_STATUS_PRIORITY.get(item.task_status, 99),
                -item.updated_at.timestamp(),
                -item.id,
            ),
        )
        current = ordered[0]
        payload = current.to_dict()
        payload["intervention_count"] = intervention_counts.get(current.id, 0)
        current_map[user_id] = payload

    return current_map, grouped


def _serialize_student_items(filters: dict, current_user) -> list[dict]:
    users = _base_student_query(filters, current_user).all()
    user_ids = [user.id for user in users]
    latest_map = latest_assessment_map(user_ids, include_top_dimension=True)
    archive_map = _archive_map(user_ids)
    current_task_map, grouped_tasks = _task_maps(user_ids)

    items = []
    for user in users:
        archive = archive_map.get(user.id)
        current_task = current_task_map.get(user.id)
        latest_assessment = latest_map.get(user.id)

        if filters.get("warning_level") and (
            not current_task or current_task["warning_level"] != filters["warning_level"]
        ):
            continue

        if filters.get("task_status") and (
            not current_task or current_task["task_status"] != filters["task_status"]
        ):
            continue

        items.append(
            {
                **user.to_dict(),
                "archive": archive,
                "latest_assessment": latest_assessment,
                "current_task": current_task,
                "task_count": len(grouped_tasks.get(user.id, [])),
            }
        )

    items.sort(
        key=lambda item: (
            WARNING_LEVEL_PRIORITY.get((item.get("current_task") or {}).get("warning_level"), 99),
            TASK_STATUS_PRIORITY.get((item.get("current_task") or {}).get("task_status"), 99),
            -float((item.get("latest_assessment") or {}).get("adjusted_score") or 0),
        )
    )
    return items


def _filter_options(current_user) -> dict:
    students = scoped_student_query(current_user).all()
    return {
        "grades": sorted({item.grade for item in students if item.grade}),
        "majors": sorted({item.major for item in students if item.major}),
        "warning_levels": list(WARNING_LEVELS),
        "task_statuses": list(TASK_STATUSES),
    }


class WorkflowOverviewResource(Resource):
    def get(self):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        filters = _request_filters()
        items = _serialize_student_items(filters, current_user)
        user_ids = [item["id"] for item in items]
        task_rows = (
            WarningTask.query.filter(WarningTask.user_id.in_(user_ids))
            .order_by(WarningTask.updated_at.desc())
            .all()
            if user_ids
            else []
        )
        record_rows = (
            InterventionRecord.query.filter(InterventionRecord.user_id.in_(user_ids))
            .order_by(InterventionRecord.created_at.desc())
            .all()
            if user_ids
            else []
        )

        summary = {
            "student_count": len(items),
            "archive_count": sum(1 for item in items if item.get("archive")),
            "pending_task_count": sum(1 for task in task_rows if task.task_status == TASK_STATUSES[0]),
            "in_progress_task_count": sum(1 for task in task_rows if task.task_status == TASK_STATUSES[1]),
            "closed_task_count": sum(1 for task in task_rows if task.task_status == TASK_STATUSES[2]),
            "intervention_count": len(record_rows),
            "urgent_count": sum(1 for task in task_rows if task.warning_level == WARNING_LEVELS[0]),
        }

        warning_level_distribution = {level: 0 for level in WARNING_LEVELS}
        task_status_distribution = {status: 0 for status in TASK_STATUSES}
        for task in task_rows:
            warning_level_distribution[task.warning_level] = warning_level_distribution.get(task.warning_level, 0) + 1
            task_status_distribution[task.task_status] = task_status_distribution.get(task.task_status, 0) + 1

        recent_tasks = []
        for task in task_rows[:8]:
            task_user = task.user.to_dict() if task.user else {}
            recent_tasks.append(
                {
                    **task.to_dict(),
                    "username": task_user.get("username"),
                    "grade": task_user.get("grade"),
                    "major": task_user.get("major"),
                    "class_name": task_user.get("class_name"),
                }
            )

        recent_records = []
        for record in record_rows[:8]:
            recent_records.append(
                {
                    **record.to_dict(),
                    "username": record.user.username if record.user else None,
                    "task_status": record.task.task_status if record.task else None,
                    "warning_level": record.task.warning_level if record.task else None,
                }
            )

        return success(
            {
                "summary": summary,
                "warning_level_distribution": warning_level_distribution,
                "task_status_distribution": task_status_distribution,
                "recent_tasks": recent_tasks,
                "recent_interventions": recent_records,
                "filter_options": _filter_options(current_user),
                "filters": filters,
            }
        )


class WorkflowStudentListResource(Resource):
    def get(self):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        filters = _request_filters()
        page = _coerce_int(request.args.get("page"), default=1, minimum=1, maximum=9999)
        page_size = _coerce_int(request.args.get("page_size"), default=10, minimum=1, maximum=50)
        items = _serialize_student_items(filters, current_user)

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size

        return success(
            {
                "items": items[start:end],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": max((total + page_size - 1) // page_size, 1),
                },
                "filter_options": _filter_options(current_user),
                "filters": filters,
            }
        )


class StudentArchiveResource(Resource):
    def get(self, user_id: int):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        user = User.query.get(user_id)
        if not user or user.role != "student":
            return error("未找到对应学生", 404)
        if not user_can_access_student(current_user, user):
            return error("当前账号无权访问该学生档案", 403)

        archive = StudentArchive.query.filter_by(user_id=user_id).first()
        if archive is None:
            archive = ensure_student_archive_for_user(user)
            db.session.commit()

        latest_assessment = latest_assessment_map([user_id], include_top_dimension=True).get(user_id)
        current_task = _task_maps([user_id])[0].get(user_id)
        return success(
            {
                "user": user.to_dict(),
                "archive": archive.to_dict(),
                "latest_assessment": latest_assessment,
                "current_task": current_task,
            }
        )

    def put(self, user_id: int):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        user = User.query.get(user_id)
        if not user or user.role != "student":
            return error("未找到对应学生", 404)
        if not user_can_access_student(current_user, user):
            return error("当前账号无权访问该学生档案", 403)

        archive = StudentArchive.query.filter_by(user_id=user_id).first()
        if archive is None:
            archive = ensure_student_archive_for_user(user)

        data = request.get_json(silent=True) or {}
        for field in (
            "advisor_name",
            "counselor_name",
            "contact_phone",
            "dormitory",
            "entry_year",
            "archive_status",
            "support_level",
            "ai_usage_pattern",
            "risk_focus",
            "notes",
        ):
            if field in data:
                setattr(archive, field, _normalize_text(data.get(field)))

        db.session.commit()
        return success(archive.to_dict(), "学生档案已更新")


class WarningTaskListResource(Resource):
    def get(self):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        query = WarningTask.query.order_by(WarningTask.updated_at.desc(), WarningTask.id.desc())
        user_id = request.args.get("user_id", type=int)
        warning_level = _normalize_text(request.args.get("warning_level"))
        task_status = _normalize_text(request.args.get("task_status"))
        accessible_ids = scoped_student_ids(current_user)

        if current_user.role == "teacher":
            if not accessible_ids:
                return success([])
            query = query.filter(WarningTask.user_id.in_(accessible_ids))

        if user_id:
            if current_user.role == "teacher" and user_id not in accessible_ids:
                return success([])
            query = query.filter(WarningTask.user_id == user_id)
        if warning_level:
            query = query.filter(WarningTask.warning_level == warning_level)
        if task_status:
            query = query.filter(WarningTask.task_status == task_status)

        items = []
        for task in query.all():
            payload = task.to_dict()
            payload["username"] = task.user.username if task.user else None
            payload["grade"] = task.user.grade if task.user else None
            payload["major"] = task.user.major if task.user else None
            payload["class_name"] = task.user.class_name if task.user else None
            items.append(payload)
        return success(items)

    def post(self):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        if not user_id:
            return error("user_id 不能为空")

        user = User.query.get(user_id)
        if not user or user.role != "student":
            return error("未找到对应学生", 404)
        if not user_can_access_student(current_user, user):
            return error("当前账号无权为该学生创建工单", 403)

        archive = ensure_student_archive_for_user(user)
        latest_assessment = latest_assessment_map([user.id], include_top_dimension=True).get(user.id)
        warning_code = _normalize_text(data.get("warning_code")) or f"MANUAL-{int(datetime.utcnow().timestamp())}-{user.id}"

        existed = WarningTask.query.filter_by(warning_code=warning_code).first()
        if existed:
            return error("预警编号已存在", 400)

        task = WarningTask(
            user_id=user.id,
            latest_assessment_id=data.get("latest_assessment_id") or (latest_assessment or {}).get("assessment_id"),
            warning_code=warning_code,
            warning_level=_normalize_text(data.get("warning_level")) or WARNING_LEVELS[-1],
            task_status=_normalize_text(data.get("task_status")) or TASK_STATUSES[0],
            source=_normalize_text(data.get("source")) or "人工创建",
            trigger_score=data.get("trigger_score") or (latest_assessment or {}).get("adjusted_score"),
            owner_name=_normalize_text(data.get("owner_name")) or archive.counselor_name,
            due_date=_parse_datetime(data.get("due_date")),
            risk_dimension=_normalize_text(data.get("risk_dimension")) or (latest_assessment or {}).get("top_dimension"),
            summary=_normalize_text(data.get("summary")) or "需要针对当前风险情况安排后续跟进。",
            recommendation=_normalize_text(data.get("recommendation")) or "建议结合评估结果和课程表现开展重点跟进。",
        )
        db.session.add(task)
        db.session.commit()
        return success(task.to_dict(), "预警工单已创建", 201)


class WarningTaskResource(Resource):
    def put(self, task_id: int):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        task = WarningTask.query.get(task_id)
        if not task:
            return error("未找到对应预警工单", 404)
        if current_user.role == "teacher" and not user_can_access_student(current_user, task.user):
            return error("当前账号无权修改该工单", 403)

        data = request.get_json(silent=True) or {}
        for field in ("warning_level", "task_status", "source", "owner_name", "risk_dimension", "summary", "recommendation"):
            if field in data:
                setattr(task, field, _normalize_text(data.get(field)))

        if "trigger_score" in data and data.get("trigger_score") is not None:
            task.trigger_score = float(data.get("trigger_score"))
        if "due_date" in data:
            task.due_date = _parse_datetime(data.get("due_date"))

        task.updated_at = datetime.utcnow()
        db.session.commit()
        return success(task.to_dict(), "预警工单已更新")


class InterventionRecordListResource(Resource):
    def get(self):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        query = InterventionRecord.query.order_by(
            InterventionRecord.created_at.desc(),
            InterventionRecord.id.desc(),
        )
        user_id = request.args.get("user_id", type=int)
        task_id = request.args.get("task_id", type=int)
        accessible_ids = scoped_student_ids(current_user)

        if current_user.role == "teacher":
            if not accessible_ids:
                return success([])
            query = query.filter(InterventionRecord.user_id.in_(accessible_ids))

        if user_id:
            if current_user.role == "teacher" and user_id not in accessible_ids:
                return success([])
            query = query.filter(InterventionRecord.user_id == user_id)
        if task_id:
            query = query.filter(InterventionRecord.task_id == task_id)

        items = []
        for record in query.all():
            payload = record.to_dict()
            payload["username"] = record.user.username if record.user else None
            payload["task_status"] = record.task.task_status if record.task else None
            payload["warning_level"] = record.task.warning_level if record.task else None
            items.append(payload)
        return success(items)

    def post(self):
        current_user, response = require_teacher_side()
        if response is not None:
            return response

        data = request.get_json(silent=True) or {}
        task_id = data.get("task_id")
        if not task_id:
            return error("task_id 不能为空")

        task = WarningTask.query.get(task_id)
        if not task:
            return error("未找到对应预警工单", 404)
        if current_user.role == "teacher" and not user_can_access_student(current_user, task.user):
            return error("当前账号无权为该工单添加干预记录", 403)

        record_content = _normalize_text(data.get("record_content"))
        intervention_method = _normalize_text(data.get("intervention_method"))
        if not record_content or not intervention_method:
            return error("干预方式和记录内容不能为空")

        record = InterventionRecord(
            task_id=task.id,
            user_id=task.user_id,
            stage=_normalize_text(data.get("stage")) or "跟进记录",
            intervention_method=intervention_method,
            record_content=record_content,
            outcome_level=_normalize_text(data.get("outcome_level")) or "待观察",
            next_action=_normalize_text(data.get("next_action")),
            follow_up_score=float(data.get("follow_up_score")) if data.get("follow_up_score") not in (None, "") else None,
            created_by=_normalize_text(data.get("created_by")) or task.owner_name,
        )
        db.session.add(record)

        archive = StudentArchive.query.filter_by(user_id=task.user_id).first()
        if archive is None and task.user is not None:
            archive = ensure_student_archive_for_user(task.user)

        if archive is not None:
            archive.last_follow_up_at = record.created_at
            if record.follow_up_score is not None:
                if record.follow_up_score >= 75:
                    archive.support_level = "专项干预"
                elif record.follow_up_score >= 55:
                    archive.support_level = "重点关注"
                else:
                    archive.support_level = "基础支持"

        task.task_status = _normalize_text(data.get("task_status")) or (
            "已闭环" if record.follow_up_score is not None and record.follow_up_score < 45 else "跟进中"
        )
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return success(record.to_dict(), "干预记录已添加", 201)


class WorkflowBootstrapResource(Resource):
    def post(self):
        _, response = require_teacher_side()
        if response is not None:
            return response

        return success(bootstrap_workflow_demo_data(), "工作流演示数据已同步", 201)
