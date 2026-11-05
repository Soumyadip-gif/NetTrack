
from datetime import datetime, timezone

from app import db


class Device(db.Model):
    """Store information about authorized local network devices."""

    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)

    ip_address = db.Column(db.String(45), nullable=False, index=True)
    mac_address = db.Column(db.String(17), nullable=True, index=True)

    hostname = db.Column(db.String(255), nullable=True)
    vendor = db.Column(db.String(150), nullable=True)
    device_type = db.Column(db.String(100), nullable=True)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="unknown"
    )

    first_seen = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_seen = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return (
            f"<Device id={self.id} "
            f"ip={self.ip_address} "
            f"status={self.status}>"
        )
