from datetime import datetime

from extensions import db


class StudentArchive(db.Model):
    __tablename__ = "student_archives"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    student_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    advisor_name = db.Column(db.String(50), nullable=True)
    counselor_name = db.Column(db.String(50), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    dormitory = db.Column(db.String(50), nullable=True)
    entry_year = db.Column(db.String(10), nullable=True)
    archive_status = db.Column(db.String(20), nullable=False, default="已建档")
    support_level = db.Column(db.String(20), nullable=False, default="基础支持")
    ai_usage_pattern = db.Column(db.String(120), nullable=True)
    risk_focus = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    last_follow_up_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "student_no": self.student_no,
            "advisor_name": self.advisor_name,
            "counselor_name": self.counselor_name,
            "contact_phone": self.contact_phone,
            "dormitory": self.dormitory,
            "entry_year": self.entry_year,
            "archive_status": self.archive_status,
            "support_level": self.support_level,
            "ai_usage_pattern": self.ai_usage_pattern,
            "risk_focus": self.risk_focus,
            "notes": self.notes,
            "last_follow_up_at": self.last_follow_up_at.isoformat() if self.last_follow_up_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WarningTask(db.Model):
    __tablename__ = "warning_tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    latest_assessment_id = db.Column(
        db.Integer,
        db.ForeignKey("assessment_results.id"),
        nullable=True,
        index=True,
    )
    warning_code = db.Column(db.String(40), nullable=False, unique=True, index=True)
    warning_level = db.Column(db.String(20), nullable=False, default="三级关注")
    task_status = db.Column(db.String(20), nullable=False, default="待处理")
    source = db.Column(db.String(30), nullable=False, default="系统评估")
    trigger_score = db.Column(db.Float, nullable=True)
    owner_name = db.Column(db.String(50), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    risk_dimension = db.Column(db.String(50), nullable=True)
    summary = db.Column(db.String(255), nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    latest_assessment = db.relationship("AssessmentResult", backref="warning_tasks", lazy=True)
    interventions = db.relationship(
        "InterventionRecord",
        backref="task",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "latest_assessment_id": self.latest_assessment_id,
            "warning_code": self.warning_code,
            "warning_level": self.warning_level,
            "task_status": self.task_status,
            "source": self.source,
            "trigger_score": round(float(self.trigger_score), 2) if self.trigger_score is not None else None,
            "owner_name": self.owner_name,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "risk_dimension": self.risk_dimension,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "intervention_count": len(self.interventions),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class InterventionRecord(db.Model):
    __tablename__ = "intervention_records"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("warning_tasks.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    stage = db.Column(db.String(30), nullable=False, default="初筛研判")
    intervention_method = db.Column(db.String(60), nullable=False)
    record_content = db.Column(db.Text, nullable=False)
    outcome_level = db.Column(db.String(20), nullable=False, default="待观察")
    next_action = db.Column(db.String(255), nullable=True)
    follow_up_score = db.Column(db.Float, nullable=True)
    created_by = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "stage": self.stage,
            "intervention_method": self.intervention_method,
            "record_content": self.record_content,
            "outcome_level": self.outcome_level,
            "next_action": self.next_action,
            "follow_up_score": round(float(self.follow_up_score), 2) if self.follow_up_score is not None else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }
