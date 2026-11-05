
from datetime import datetime, timezone

from app import db


class SpeedTest(db.Model):
    """Store internet speed test results."""

    __tablename__ = "speed_tests"

    id = db.Column(db.Integer, primary_key=True)

    download_speed = db.Column(db.Float, nullable=False)
    upload_speed = db.Column(db.Float, nullable=False)

    ping = db.Column(db.Float, nullable=True)
    jitter = db.Column(db.Float, nullable=True)

    server_name = db.Column(db.String(150), nullable=True)
    server_location = db.Column(db.String(150), nullable=True)

    isp_name = db.Column(db.String(150), nullable=True)
    public_ip = db.Column(db.String(45), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return (
            f"<SpeedTest id={self.id} "
            f"download={self.download_speed} "
            f"upload={self.upload_speed}>"
        )
