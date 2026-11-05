
from datetime import datetime, timezone

from app import db


class LocationSpeedTest(db.Model):
    """Store user-measured network speeds at geographical locations."""

    __tablename__ = "location_speed_tests"

    id = db.Column(db.Integer, primary_key=True)

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    download_speed = db.Column(db.Float, nullable=False)
    upload_speed = db.Column(db.Float, nullable=False)

    ping = db.Column(db.Float, nullable=True)
    jitter = db.Column(db.Float, nullable=True)

    provider = db.Column(db.String(50), nullable=True)
    connection_type = db.Column(db.String(30), nullable=True)

    accuracy = db.Column(db.Float, nullable=True)

    source_type = db.Column(
        db.String(30),
        nullable=False,
        default="user_measured"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return (
            f"<LocationSpeedTest id={self.id} "
            f"provider={self.provider} "
            f"download={self.download_speed}>"
        )
