
from datetime import datetime, timezone

from app import db


class NetworkAlert(db.Model):
    """Store network alerts and their resolution status."""

    __tablename__ = "network_alerts"

    id = db.Column(db.Integer, primary_key=True)

    alert_type = db.Column(db.String(100), nullable=False)

    severity = db.Column(
        db.String(20),
        nullable=False,
        default="info"
    )

    message = db.Column(db.Text, nullable=False)

    is_resolved = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    resolved_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self):
        return (
            f"<NetworkAlert id={self.id} "
            f"type={self.alert_type} "
            f"severity={self.severity}>"
        )
