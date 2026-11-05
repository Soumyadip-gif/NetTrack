
from datetime import datetime, timezone

from app import db


class NetworkMetric(db.Model):
    """Store historical network performance measurements."""

    __tablename__ = "network_metrics"

    id = db.Column(db.Integer, primary_key=True)

    download_speed = db.Column(db.Float, nullable=True)
    upload_speed = db.Column(db.Float, nullable=True)

    ping = db.Column(db.Float, nullable=True)
    jitter = db.Column(db.Float, nullable=True)
    packet_loss = db.Column(db.Float, nullable=True)

    interface = db.Column(db.String(100), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return (
            f"<NetworkMetric id={self.id} "
            f"download={self.download_speed} "
            f"upload={self.upload_speed}>"
        )
