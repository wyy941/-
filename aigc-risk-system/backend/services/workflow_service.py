from __future__ import annotations

import json
from datetime import datetime, timedelta

from extensions import db
from models.assessment import AssessmentResult
from models.user import User
from models.workflow import InterventionRecord, StudentArchive, WarningTask
from services.cache_service import cache_delete_prefix
from services.risk_engine import DIMENSION_LABELS, FEATURE_LABELS

WARNING_LEVELS = ("一级预警", "二级预警", "三级关注")
TASK_STATUSES = ("待处理", "跟进中", "已闭环")
SUPPORT_LEVELS = ("基础支持", "重点关注", "专项干预")
ADVISOR_POOL = (
    "陈明",
    "李娜",
    "周航",
    "赵珊",
    "吴楠",
    "张宁",
)
COUNSELOR_POOL = (
    "王老师",
    "刘老师",
    "孙老师",
    "郑老师",
)
DORMITORY_POOL = (
    "兰苑1舍",
    "竹苑2舍",
    "松苑3舍",
    "桂苑4舍",
    "和苑5舍",
)
USAGE_PATTERNS = (
    "课程作业辅助 + 资料整理",
    "编程调试 + 报告润色",
    "文献综述 + 思路启发",
    "课堂复习 + 自测问答",
)


def _latest_assessment_for_user(user_id: int) -> AssessmentResult | None:
    return (
        AssessmentResult.query.filter_by(user_id=user_id)
        .order_by(AssessmentResult.created_at.desc(), AssessmentResult.id.desc())
        .first()
    )


def _student_no_for_user(user: User) -> str:
    grade = (user.grade or str(datetime.utcnow().year))[:4]
    if user.username and user.username.isdigit() and len(user.username) >= 8:
        return user.username
    return f"{grade}{user.id:06d}"


def _risk_focus_from_assessment(assessment: AssessmentResult | None) -> str:
    if assessment is None:
        return "待补充评估记录"

    details = json.loads(assessment.details_json or "{}")
    rows = sorted(
        details.items(),
        key=lambda item: float(item[1]),
        reverse=True,
    )[:2]
    if not rows:
        return "当前暂无显著风险焦点"
    return "；".join(f"{FEATURE_LABELS.get(code, code)} {round(float(score), 1)}" for code, score in rows)


def _top_dimension_name(assessment: AssessmentResult | None) -> str:
    if assessment is None:
        return "待评估"

    details = json.loads(assessment.details_json or "{}")
    if not details:
        return "待评估"

    dimension_scores: dict[str, list[float]] = {}
    for code, score in details.items():
        dimension = "custom"
        if code in FEATURE_LABELS:
            from services.risk_engine import FEATURE_DIMENSIONS

            dimension = FEATURE_DIMENSIONS.get(code, "custom")
        dimension_scores.setdefault(dimension, []).append(float(score))

    ranked = sorted(
        (
            (dimension, sum(scores) / max(len(scores), 1))
            for dimension, scores in dimension_scores.items()
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    if not ranked:
        return "待评估"
    return DIMENSION_LABELS.get(ranked[0][0], ranked[0][0])


def _support_level_from_assessment(assessment: AssessmentResult | None) -> str:
    if assessment is None:
        return "基础支持"
    if assessment.risk_level == "高风险" or float(assessment.adjusted_score) >= 75:
        return "专项干预"
    if assessment.risk_level == "中风险" or float(assessment.adjusted_score) >= 55:
        return "重点关注"
    return "基础支持"


def ensure_student_archive_for_user(user: User) -> StudentArchive:
    archive = StudentArchive.query.filter_by(user_id=user.id).first()
    latest_assessment = _latest_assessment_for_user(user.id)
    latest_intervention = (
        InterventionRecord.query.filter_by(user_id=user.id)
        .order_by(InterventionRecord.created_at.desc(), InterventionRecord.id.desc())
        .first()
    )

    if archive is None:
        archive = StudentArchive(user_id=user.id, student_no=_student_no_for_user(user))
        db.session.add(archive)

    advisor_name = ADVISOR_POOL[user.id % len(ADVISOR_POOL)]
    counselor_name = COUNSELOR_POOL[user.id % len(COUNSELOR_POOL)]
    dormitory = DORMITORY_POOL[user.id % len(DORMITORY_POOL)]
    usage_pattern = USAGE_PATTERNS[user.id % len(USAGE_PATTERNS)]

    archive.student_no = archive.student_no or _student_no_for_user(user)
    archive.advisor_name = archive.advisor_name or advisor_name
    archive.counselor_name = archive.counselor_name or counselor_name
    archive.contact_phone = archive.contact_phone or f"13{(user.id * 37) % 10**9:09d}"
    archive.dormitory = archive.dormitory or dormitory
    archive.entry_year = user.grade or archive.entry_year
    archive.archive_status = archive.archive_status or "已建档"
    archive.support_level = _support_level_from_assessment(latest_assessment)
    archive.ai_usage_pattern = archive.ai_usage_pattern or usage_pattern
    archive.risk_focus = _risk_focus_from_assessment(latest_assessment)
    archive.notes = archive.notes or "已纳入 AIGC 风险持续跟踪档案。"
    archive.last_follow_up_at = (
        latest_intervention.created_at
        if latest_intervention
        else latest_assessment.created_at if latest_assessment else archive.last_follow_up_at
    )
    return archive


def ensure_student_archives() -> dict:
    students = User.query.filter_by(role="student").order_by(User.id.asc()).all()
    created_count = 0
    updated_count = 0

    for user in students:
        before = StudentArchive.query.filter_by(user_id=user.id).first()
        ensure_student_archive_for_user(user)
        if before is None:
            created_count += 1
        else:
            updated_count += 1

    db.session.commit()
    return {
        "total_students": len(students),
        "created_count": created_count,
        "updated_count": updated_count,
    }


def _warning_level_from_assessment(assessment: AssessmentResult | None) -> str | None:
    if assessment is None:
        return None
    score = float(assessment.adjusted_score or 0)
    if assessment.risk_level == "高风险" or score >= 75:
        return "一级预警"
    if assessment.risk_level == "中风险" or score >= 60:
        return "二级预警"
    if score >= 45:
        return "三级关注"
    return None


def _task_summary(assessment: AssessmentResult | None) -> str:
    if assessment is None:
        return "待补充风险评估后生成预警摘要"
    return f"{_top_dimension_name(assessment)}维度风险偏高，需启动后续跟踪。"


def _task_recommendation(assessment: AssessmentResult | None) -> str:
    if assessment is None:
        return "建议尽快补充测评，完成首次干预研判。"
    suggestions = json.loads(assessment.suggestions_json or "[]")
    return "；".join(suggestions[:2]) if suggestions else "建议结合课程任务与导师反馈制定干预计划。"


def _parse_task_due_date(assessment: AssessmentResult | None, warning_level: str) -> datetime:
    base_time = assessment.created_at if assessment is not None else datetime.utcnow()
    if warning_level == "一级预警":
        return base_time + timedelta(days=3)
    if warning_level == "二级预警":
        return base_time + timedelta(days=7)
    return base_time + timedelta(days=14)


def sync_warning_task_for_user(user_id: int) -> WarningTask | None:
    user = User.query.get(user_id)
    if user is None or user.role != "student":
        return None

    archive = ensure_student_archive_for_user(user)
    latest_assessment = _latest_assessment_for_user(user.id)
    warning_level = _warning_level_from_assessment(latest_assessment)

    if warning_level is None:
        current_task = (
            WarningTask.query.filter_by(user_id=user.id)
            .order_by(WarningTask.updated_at.desc(), WarningTask.id.desc())
            .first()
        )
        if current_task and current_task.task_status != "已闭环":
            current_task.task_status = "已闭环"
            current_task.updated_at = datetime.utcnow()
            db.session.commit()
        return None

    warning_code = f"WARN-{latest_assessment.id:06d}" if latest_assessment else f"WARN-{user.id:06d}"
    task = WarningTask.query.filter_by(warning_code=warning_code).first()
    if task is None:
        task = WarningTask(
            user_id=user.id,
            latest_assessment_id=latest_assessment.id if latest_assessment else None,
            warning_code=warning_code,
            task_status="待处理",
        )
        db.session.add(task)

    task.latest_assessment_id = latest_assessment.id if latest_assessment else None
    task.warning_level = warning_level
    task.source = "系统评估"
    task.trigger_score = float(latest_assessment.adjusted_score) if latest_assessment else None
    task.owner_name = archive.counselor_name or archive.advisor_name
    task.due_date = _parse_task_due_date(latest_assessment, warning_level)
    task.risk_dimension = _top_dimension_name(latest_assessment)
    task.summary = _task_summary(latest_assessment)
    task.recommendation = _task_recommendation(latest_assessment)
    task.updated_at = datetime.utcnow()
    return task


def _seed_records_for_task(task: WarningTask, archive: StudentArchive) -> list[InterventionRecord]:
    if task.interventions:
        return []

    trigger_score = float(task.trigger_score or 0)
    stage_templates = [
        (
            "初筛研判",
            "系统筛查",
            f"结合最近一次测评结果，对 {task.summary or '当前风险'} 进行初筛研判，确定重点跟进方向。",
            "待观察",
            "安排导师或辅导员进行第一次访谈",
            max(trigger_score - 3, 0),
        ),
        (
            "导师访谈",
            "谈心访谈",
            f"由 {task.owner_name or archive.counselor_name or archive.advisor_name or '责任教师'} 开展一对一访谈，"
            f"聚焦 {archive.risk_focus or '核心风险指标'}。",
            "待观察",
            "结合课程任务设置阶段性使用边界",
            max(trigger_score - 6, 0),
        ),
        (
            "跟踪复评",
            "阶段复盘",
            "复盘近期学习任务完成情况与 AIGC 使用边界执行情况，评估干预效果。",
            "已改善" if task.warning_level != "一级预警" else "需升级",
            "视风险变化决定是否继续跟踪或闭环",
            max(trigger_score - (12 if task.warning_level != "一级预警" else 5), 0),
        ),
    ]

    if task.warning_level == "三级关注":
        use_count = 1 if task.user_id % 2 == 0 else 2
    elif task.warning_level == "二级预警":
        use_count = 2
    else:
        use_count = 3

    records = []
    for index, template in enumerate(stage_templates[:use_count]):
        created_at = task.created_at + timedelta(days=index * 4 + 1)
        stage, method, content, outcome, next_action, follow_up_score = template
        records.append(
            InterventionRecord(
                task_id=task.id,
                user_id=task.user_id,
                stage=stage,
                intervention_method=method,
                record_content=content,
                outcome_level=outcome,
                next_action=next_action,
                follow_up_score=follow_up_score,
                created_by=task.owner_name,
                created_at=created_at,
            )
        )

    if use_count == 1:
        task.task_status = "待处理"
    elif use_count == 2:
        task.task_status = "跟进中"
    else:
        task.task_status = "已闭环" if task.user_id % 2 == 0 else "跟进中"

    archive.last_follow_up_at = records[-1].created_at if records else archive.last_follow_up_at
    return records


def bootstrap_workflow_demo_data() -> dict:
    students = User.query.filter_by(role="student").order_by(User.id.asc()).all()
    created_tasks = 0
    created_records = 0

    for user in students:
        archive = ensure_student_archive_for_user(user)
        before_task = WarningTask.query.filter_by(user_id=user.id).count()
        task = sync_warning_task_for_user(user.id)
        if task is not None:
            db.session.flush()
            after_task = WarningTask.query.filter_by(user_id=user.id).count()
            if after_task > before_task:
                created_tasks += 1
            records = _seed_records_for_task(task, archive)
            if records:
                db.session.add_all(records)
                created_records += len(records)

    db.session.commit()
    cache_delete_prefix("dashboard:overview:")
    return {
        "archive_count": StudentArchive.query.count(),
        "task_count": WarningTask.query.count(),
        "intervention_count": InterventionRecord.query.count(),
        "created_tasks": created_tasks,
        "created_records": created_records,
    }
