from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    grade = db.Column(db.String(20), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    class_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assessments = db.relationship("AssessmentResult", backref="user", lazy=True)
    archive = db.relationship(
        "StudentArchive",
        backref="user",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )
    teacher_assignments = db.relationship(
        "TeacherAssignment",
        backref="teacher",
        lazy=True,
        cascade="all, delete-orphan",
        foreign_keys="TeacherAssignment.teacher_id",
    )
    warning_tasks = db.relationship("WarningTask", backref="user", lazy=True)
    intervention_records = db.relationship("InterventionRecord", backref="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "grade": self.grade,
            "major": self.major,
            "class_name": self.class_name,
            "teacher_assignments": (
                [
                    item.to_dict()
                    for item in sorted(
                        self.teacher_assignments,
                        key=lambda current: (
                            current.grade or "",
                            current.major or "",
                            current.class_name or "",
                        ),
                    )
                ]
                if self.role == "teacher"
                else []
            ),
            "created_at": self.created_at.isoformat(),
        }


class TeacherAssignment(db.Model):
    __tablename__ = "teacher_assignments"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    grade = db.Column(db.String(20), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    class_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "grade": self.grade,
            "major": self.major,
            "class_name": self.class_name,
            "created_at": self.created_at.isoformat(),
        }
