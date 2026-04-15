from datetime import datetime

from extensions import db


class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_score = db.Column(db.Float, nullable=False)
    adjusted_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    details_json = db.Column(db.Text, nullable=False)
    suggestions_json = db.Column(db.Text, nullable=False)
    source_payload_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_score": self.total_score,
            "adjusted_score": self.adjusted_score,
            "risk_level": self.risk_level,
            "details_json": self.details_json,
            "suggestions_json": self.suggestions_json,
            "source_payload_json": self.source_payload_json,
            "created_at": self.created_at.isoformat(),
        }
