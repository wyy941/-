from app import app
from extensions import db
from models.indicator import Indicator
from models.user import User
from services.risk_engine import DEFAULT_INDICATORS
from services.sample_data_service import (
    DEFAULT_SAMPLE_STUDENT_COUNT,
    generate_realistic_sample_csv,
    import_sample_data,
    reset_legacy_sample_data,
)
from services.teacher_scope_service import sync_default_teacher_assignments


def _ensure_demo_users() -> None:
    demo_users = [
        {
            "username": "admin",
            "password": "123456",
            "role": "admin",
            "grade": None,
            "major": "软件工程",
            "class_name": "管理端",
        },
        {
            "username": "teacher1",
            "password": "123456",
            "role": "teacher",
            "grade": None,
            "major": "学生事务管理",
            "class_name": "教师端",
        },
        {
            "username": "student1",
            "password": "123456",
            "role": "student",
            "grade": "2022",
            "major": "软件工程",
            "class_name": "2022级软件工程1班",
        },
    ]

    usernames = [item["username"] for item in demo_users]
    existing_users = {
        user.username: user for user in User.query.filter(User.username.in_(usernames)).all()
    }
    for item in demo_users:
        user = existing_users.get(item["username"])
        if not user:
            user = User(username=item["username"])
            user.set_password(item["password"])
            db.session.add(user)
            existing_users[item["username"]] = user

        user.role = item["role"]
        user.grade = item["grade"]
        user.major = item["major"]
        user.class_name = item["class_name"]


def _sync_teacher_assignments() -> None:
    sync_default_teacher_assignments()


def _sync_indicators() -> None:
    for item in DEFAULT_INDICATORS:
        indicator = Indicator.query.filter_by(code=item["code"]).first()
        if not indicator:
            db.session.add(
                Indicator(
                    code=item["code"],
                    name=item["name"],
                    weight=item["weight"],
                    description=item["description"],
                    score_standard=item.get("score_standard"),
                    enabled=True,
                )
            )
            continue

        indicator.name = item["name"]
        indicator.weight = item["weight"]
        indicator.description = item["description"]
        indicator.score_standard = item.get("score_standard")
        indicator.enabled = True


def run():
    with app.app_context():
        db.create_all()
        _ensure_demo_users()
        _sync_teacher_assignments()
        _sync_indicators()
        db.session.commit()

        cleanup = reset_legacy_sample_data()
        dataset = generate_realistic_sample_csv(
            overwrite=True,
            student_count=DEFAULT_SAMPLE_STUDENT_COUNT,
        )
        result = import_sample_data()

        print("初始化完成：默认用户 admin / teacher1 / student1，密码均为 123456")
        print(
            f"已生成真实样本文件，共 {dataset['total_rows']} 条记录，"
            f"覆盖 {dataset['covered_users']} 名学生"
        )
        if cleanup["removed_users"] or cleanup["removed_assessments"]:
            print(
                f"已清理旧版样本用户 {cleanup['removed_users']} 个，"
                f"移除历史评估 {cleanup['removed_assessments']} 条"
            )
        print(
            f"示例数据导入完成，新增评估 {result['imported_count']} 条，"
            f"跳过重复 {result['skipped_count']} 条，"
            f"新建用户 {result['created_user_count']} 个"
        )


if __name__ == "__main__":
    run()
