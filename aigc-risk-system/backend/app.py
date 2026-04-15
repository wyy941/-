from flask import Flask
from flask_cors import CORS
from flask_restful import Api

from config import Config
from extensions import db
from models.indicator import Indicator
from models.user import User
from resources.assessment import (
    AssessmentHistoryResource,
    EvaluateAssessmentResource,
    StudentSelfAssessmentMetaResource,
    StudentSelfAssessmentResource,
)
from resources.auth import LoginResource, RegisterResource
from resources.dashboard import OverviewDashboardResource, UserTrendResource
from resources.data import SampleDataImportResource, SampleDataPreviewResource
from resources.indicator import IndicatorListResource, IndicatorResource
from resources.report import (
    AssessmentReportExportResource,
    AssessmentReportResource,
    LatestReportResource,
)
from resources.user import (
    TeacherAssignmentOptionsResource,
    TeacherAssignmentResource,
    TeacherListResource,
    UserListResource,
    UserProfileResource,
    UserQueryResource,
)
from resources.workflow import (
    InterventionRecordListResource,
    StudentArchiveResource,
    WarningTaskListResource,
    WarningTaskResource,
    WorkflowBootstrapResource,
    WorkflowOverviewResource,
    WorkflowStudentListResource,
)
from services.risk_engine import DEFAULT_INDICATORS
from services.teacher_scope_service import sync_default_teacher_assignments


def sync_default_indicators() -> None:
    changed = False
    for item in DEFAULT_INDICATORS:
        indicator = Indicator.query.filter_by(code=item["code"]).first()
        if indicator is None:
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
            changed = True
            continue

        indicator.name = item["name"]
        indicator.weight = item["weight"]
        indicator.description = item["description"]
        indicator.score_standard = item.get("score_standard")
        indicator.enabled = True
        changed = True

    if changed:
        db.session.commit()


def sync_default_demo_users() -> None:
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
            "class_name": "2022级软工1班",
        },
    ]

    usernames = [item["username"] for item in demo_users]
    existing_users = {
        user.username: user for user in User.query.filter(User.username.in_(usernames)).all()
    }
    changed = False
    for item in demo_users:
        user = existing_users.get(item["username"])
        if user is None:
            user = User(username=item["username"])
            user.set_password(item["password"])
            db.session.add(user)
            existing_users[item["username"]] = user
            changed = True

        for field in ("role", "grade", "major", "class_name"):
            if getattr(user, field) != item[field]:
                setattr(user, field, item[field])
                changed = True

    if changed:
        db.session.commit()


def sync_demo_teacher_assignments() -> None:
    if sync_default_teacher_assignments():
        db.session.commit()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    api = Api(app)

    api.add_resource(RegisterResource, "/api/auth/register")
    api.add_resource(LoginResource, "/api/auth/login")
    api.add_resource(UserListResource, "/api/users")
    api.add_resource(UserQueryResource, "/api/users/query")
    api.add_resource(UserProfileResource, "/api/users/profile")
    api.add_resource(TeacherListResource, "/api/teachers")
    api.add_resource(TeacherAssignmentOptionsResource, "/api/teachers/assignment-options")
    api.add_resource(TeacherAssignmentResource, "/api/teachers/<int:teacher_id>/assignments")

    api.add_resource(IndicatorListResource, "/api/indicators")
    api.add_resource(IndicatorResource, "/api/indicators/<int:indicator_id>")

    api.add_resource(EvaluateAssessmentResource, "/api/assessments/evaluate")
    api.add_resource(AssessmentHistoryResource, "/api/assessments/history/<int:user_id>")
    api.add_resource(StudentSelfAssessmentMetaResource, "/api/students/self-assessment/meta")
    api.add_resource(StudentSelfAssessmentResource, "/api/students/self-assessment")
    api.add_resource(LatestReportResource, "/api/reports/latest/<int:user_id>")
    api.add_resource(AssessmentReportResource, "/api/reports/assessment/<int:assessment_id>")
    api.add_resource(
        AssessmentReportExportResource,
        "/api/reports/assessment/<int:assessment_id>/export",
    )

    api.add_resource(OverviewDashboardResource, "/api/dashboard/overview")
    api.add_resource(UserTrendResource, "/api/dashboard/trend/<int:user_id>")
    api.add_resource(SampleDataPreviewResource, "/api/data/sample-preview")
    api.add_resource(SampleDataImportResource, "/api/data/import-sample")
    api.add_resource(WorkflowOverviewResource, "/api/workflows/overview")
    api.add_resource(WorkflowStudentListResource, "/api/workflows/students")
    api.add_resource(StudentArchiveResource, "/api/workflows/archives/<int:user_id>")
    api.add_resource(WarningTaskListResource, "/api/workflows/tasks")
    api.add_resource(WarningTaskResource, "/api/workflows/tasks/<int:task_id>")
    api.add_resource(InterventionRecordListResource, "/api/workflows/interventions")
    api.add_resource(WorkflowBootstrapResource, "/api/workflows/bootstrap")

    @app.get("/")
    def home():
        return {
            "project": "大学生AIGC技术依赖风险评估系统",
            "message": "后端服务已启动",
            "api_base": "/api",
            "sample_data": app.config["SAMPLE_DATA_PATH"],
        }

    with app.app_context():
        db.create_all()
        sync_default_indicators()
        sync_default_demo_users()
        sync_demo_teacher_assignments()

    return app


app = create_app()


def run_local_server() -> None:
    try:
        from waitress import serve
    except ImportError:
        app.run(debug=True)
        return

    print("Serving on http://127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    run_local_server()
