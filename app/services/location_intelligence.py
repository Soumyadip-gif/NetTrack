from pathlib import Path
from datetime import datetime, timezone
import math

from flask import request, jsonify, current_app
from app import db
from app.models import LocationSpeedTest


def _number(value):
    if isinstance(value, bool):
        raise ValueError("Invalid numeric value.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Invalid numeric value.")
    return result


def _distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def save_location_speed_test(payload):
    latitude = _number(payload.get("latitude"))
    longitude = _number(payload.get("longitude"))
    download = _number(payload.get("download_mbps"))
    upload = _number(payload.get("upload_mbps"))
    accuracy = _number(payload.get("accuracy_m"))

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Invalid GPS coordinates.")
    if not 0 <= download <= 100000 or not 0 <= upload <= 100000:
        raise ValueError("Speed values are outside the accepted range.")
    if not 0 < accuracy <= 100:
        raise ValueError("GPS accuracy must be 100 metres or better.")

    ping = payload.get("ping_ms")
    jitter = payload.get("jitter_ms")
    ping = _number(ping) if ping is not None else None
    jitter = _number(jitter) if jitter is not None else None

    if ping is not None and not 0 <= ping <= 60000:
        raise ValueError("Invalid ping value.")
    if jitter is not None and not 0 <= jitter <= 60000:
        raise ValueError("Invalid jitter value.")

    provider = str(payload.get("provider") or "").strip()[:50] or None
    connection_type = str(payload.get("connection_type") or "").strip()[:30] or None

    record = LocationSpeedTest(
        latitude=latitude,
        longitude=longitude,
        download_speed=download,
        upload_speed=upload,
        ping=ping,
        jitter=jitter,
        accuracy=accuracy,
        provider=provider,
        connection_type=connection_type,
        source_type="user_measured",
    )

    db.session.add(record)
    db.session.commit()

    return record


def find_best_nearby_spots(latitude, longitude, radius_km=3):
    latitude = _number(latitude)
    longitude = _number(longitude)
    radius_km = _number(radius_km)

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Invalid search coordinates.")
    if radius_km not in (0.5, 1, 3, 5, 10):
        raise ValueError("Choose a supported search radius.")

    lat_delta = radius_km / 110.574
    lon_scale = max(0.01, 111.320 * abs(math.cos(math.radians(latitude))))
    lon_delta = radius_km / lon_scale

    records = LocationSpeedTest.query.filter(
        LocationSpeedTest.latitude.between(
            max(-90, latitude - lat_delta),
            min(90, latitude + lat_delta)
        ),
        LocationSpeedTest.longitude.between(
            max(-180, longitude - lon_delta),
            min(180, longitude + lon_delta)
        ),
        LocationSpeedTest.source_type == "user_measured"
    ).all()

    # Group nearby measurements into approximate 100-metre map cells.
    groups = {}
    for record in records:
        distance = _distance_km(
            latitude, longitude, record.latitude, record.longitude
        )
        if distance > radius_km:
            continue

        key = (round(record.latitude, 3), round(record.longitude, 3))
        groups.setdefault(key, []).append((record, distance))

    results = []
    now = datetime.now(timezone.utc)

    for (cell_lat, cell_lon), entries in groups.items():
        measurements = [item[0] for item in entries]
        distance = _distance_km(latitude, longitude, cell_lat, cell_lon)

        downloads = [item.download_speed for item in measurements]
        uploads = [item.upload_speed for item in measurements]
        pings = [item.ping for item in measurements if item.ping is not None]

        latest = max(
            (item.created_at for item in measurements if item.created_at),
            default=None
        )
        if latest and latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)

        age_days = max(0, (now - latest).total_seconds() / 86400) if latest else 365
        freshness = max(0.1, 1 - age_days / 30)

        results.append({
            "latitude": round(sum(item.latitude for item in measurements) / len(measurements), 6),
            "longitude": round(sum(item.longitude for item in measurements) / len(measurements), 6),
            "distance_km": round(distance, 3),
            "download_mbps": round(sum(downloads) / len(downloads), 2),
            "upload_mbps": round(sum(uploads) / len(uploads), 2),
            "ping_ms": round(sum(pings) / len(pings), 2) if pings else None,
            "test_count": len(measurements),
            "last_tested": latest.isoformat() if latest else None,
            "freshness": round(freshness, 2),
            "reliability": "Low" if len(measurements) < 3 else ("Medium" if len(measurements) < 10 else "Higher"),
        })

    if results:
        max_download = max(item["download_mbps"] for item in results) or 1
        max_upload = max(item["upload_mbps"] for item in results) or 1

        for item in results:
            download_score = item["download_mbps"] / max_download
            upload_score = item["upload_mbps"] / max_upload
            ping_score = (
                1 / (1 + item["ping_ms"] / 100)
                if item["ping_ms"] is not None else 0.5
            )
            sample_score = min(item["test_count"] / 5, 1)
            distance_score = max(0, 1 - item["distance_km"] / radius_km)

            item["score"] = round(
                100 * (
                    0.40 * download_score
                    + 0.15 * upload_score
                    + 0.20 * ping_score
                    + 0.15 * sample_score
                    + 0.10 * distance_score
                ) * item["freshness"],
                1
            )

        results.sort(key=lambda item: item["score"], reverse=True)

    return results
