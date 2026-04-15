from datetime import datetime

from extensions import db
from services.risk_engine import get_indicator_meta


class Indicator(db.Model):
    __tablename__ = "indicators"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False, default=0.1)
    description = db.Column(db.Text, nullable=True)
    score_standard = db.Column(db.Text, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        meta = get_indicator_meta(self.code)
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "weight": self.weight,
            "description": self.description,
            "score_standard": self.score_standard,
            "dimension": meta.get("dimension", "custom"),
            "dimension_name": meta.get("dimension_name", "自定义指标"),
            "default_suggestion": meta.get("suggestion"),
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
        }
