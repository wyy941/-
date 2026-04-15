from __future__ import annotations

from sqlalchemy import and_, false, or_

from extensions import db
from models.user import TeacherAssignment, User

DEFAULT_TEACHER_ASSIGNMENTS = {
    "teacher1": [
        {"grade": "2022", "major": "软件工程", "class_name": "2022级软工1班"},
        {"grade": "2022", "major": "软件工程", "class_name": "2022级软工2班"},
        {"grade": "2023", "major": "人工智能", "class_name": "2023级人工智能1班"},
        {"grade": "2024", "major": "人工智能", "class_name": "2024级人工智能1班"},
    ]
}


def _normalize_scope_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalized_assignment_specs(assignments: list[dict] | None) -> list[dict]:
    normalized = []
    seen = set()

    for item in assignments or []:
        grade = _normalize_scope_value(item.get("grade"))
        major = _normalize_scope_value(item.get("major"))
        class_name = _normalize_scope_value(item.get("class_name"))
        if not any([grade, major, class_name]):
            continue

        signature = (grade, major, class_name)
        if signature in seen:
            continue

        seen.add(signature)
        normalized.append(
            {
                "grade": grade,
                "major": major,
                "class_name": class_name,
            }
        )

    normalized.sort(
        key=lambda item: (
            item["grade"] or "",
            item["major"] or "",
            item["class_name"] or "",
        )
    )
    return normalized


def teacher_scope_assignments(user: User | None) -> list[TeacherAssignment]:
    if user is None or user.role != "teacher":
        return []
    return sorted(
        user.teacher_assignments,
        key=lambda item: (
            item.grade or "",
            item.major or "",
            item.class_name or "",
        ),
    )


def teacher_scope_signature(user: User | None) -> str:
    if user is None:
        return "anonymous"
    if user.role != "teacher":
        return f"{user.role}:{user.id}"

    assignments = teacher_scope_assignments(user)
    if not assignments:
        return f"teacher:{user.id}:unassigned"

    joined = "|".join(
        f"{item.grade or '*'}:{item.major or '*'}:{item.class_name or '*'}"
        for item in assignments
    )
    return f"teacher:{user.id}:{joined}"


def sync_teacher_assignments(user: User, assignments: list[dict] | None) -> bool:
    if user.role != "teacher":
        return False

    desired = _normalized_assignment_specs(assignments)
    existing = {
        (item.grade, item.major, item.class_name): item for item in user.teacher_assignments
    }
    desired_signatures = {
        (item["grade"], item["major"], item["class_name"]) for item in desired
    }

    changed = False
    for signature, assignment in list(existing.items()):
        if signature not in desired_signatures:
            db.session.delete(assignment)
            changed = True

    for item in desired:
        signature = (item["grade"], item["major"], item["class_name"])
        if signature in existing:
            continue
        user.teacher_assignments.append(
            TeacherAssignment(
                grade=item["grade"],
                major=item["major"],
                class_name=item["class_name"],
            )
        )
        changed = True

    return changed


def sync_default_teacher_assignments() -> bool:
    usernames = list(DEFAULT_TEACHER_ASSIGNMENTS.keys())
    teachers = {
        user.username: user for user in User.query.filter(User.username.in_(usernames)).all()
    }

    changed = False
    for username, assignments in DEFAULT_TEACHER_ASSIGNMENTS.items():
        teacher = teachers.get(username)
        if teacher is None:
            continue
        changed = sync_teacher_assignments(teacher, assignments) or changed

    return changed


def user_can_access_student(current_user: User | None, target_user: User | None) -> bool:
    if current_user is None or target_user is None:
        return False

    if current_user.role == "admin":
        return True

    if current_user.role == "student":
        return current_user.id == target_user.id

    if current_user.role != "teacher" or target_user.role != "student":
        return False

    for assignment in teacher_scope_assignments(current_user):
        if assignment.grade and assignment.grade != target_user.grade:
            continue
        if assignment.major and assignment.major != target_user.major:
            continue
        if assignment.class_name and assignment.class_name != target_user.class_name:
            continue
        return True

    return False


def scoped_student_query(current_user: User | None, query=None):
    query = query or User.query
    query = query.filter(User.role == "student")

    if current_user is None:
        return query.filter(false())

    if current_user.role == "admin":
        return query

    if current_user.role == "student":
        return query.filter(User.id == current_user.id)

    if current_user.role != "teacher":
        return query.filter(false())

    clauses = []
    for assignment in teacher_scope_assignments(current_user):
        filters = []
        if assignment.grade:
            filters.append(User.grade == assignment.grade)
        if assignment.major:
            filters.append(User.major == assignment.major)
        if assignment.class_name:
            filters.append(User.class_name == assignment.class_name)
        if filters:
            clauses.append(and_(*filters))

    if not clauses:
        return query.filter(false())

    return query.filter(or_(*clauses))


def scoped_student_ids(current_user: User | None) -> list[int]:
    rows = scoped_student_query(current_user).with_entities(User.id).all()
    return [item.id for item in rows]
