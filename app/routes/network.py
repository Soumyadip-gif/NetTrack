
import json
from pathlib import Path

import psutil

from flask import Blueprint, jsonify, current_app, request

from app import db
from app.models import NetworkMetric
from app.services.network_monitor import network_monitor
from app.services.wifi_scanner import scan_wifi_networks


network_bp = Blueprint("network", __name__)


@network_bp.route("/api/network/stats", methods=["GET"])
def network_stats():
    """Return current network interface and traffic statistics."""

    try:
        data = network_monitor.get_network_stats()

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Unable to collect network statistics."
        }), 500


@network_bp.route("/api/network/history", methods=["GET"])
def network_history():
    """Return the latest 100 historical network measurements."""

    try:
        records = (
            NetworkMetric.query
            .order_by(NetworkMetric.created_at.desc())
            .limit(100)
            .all()
        )

        history = [
            {
                "id": record.id,
                "interface": record.interface,
                "download_mbps": record.download_speed,
                "upload_mbps": record.upload_speed,
                "timestamp": (
                    record.created_at.isoformat()
                    if record.created_at else None
                ),
            }
            for record in records
        ]

        return jsonify({
            "success": True,
            "total": len(history),
            "data": history,
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Unable to retrieve network history."
        }), 500


@network_bp.route("/api/network/status", methods=["GET"])
def network_status():
    """Return background monitoring worker status."""

    try:
        status_file = (
            Path(current_app.instance_path)
            / "monitor_status.json"
        )

        status = {}

        if status_file.exists():
            status = json.loads(
                status_file.read_text(encoding="utf-8")
            )

        pid = status.get("pid")
        worker_running = (
            status.get("running", False)
            and isinstance(pid, int)
            and psutil.pid_exists(pid)
        )

        total_measurements = NetworkMetric.query.count()

        return jsonify({
            "success": True,
            "data": {
                "running": worker_running,
                "worker_pid": pid,
                "interval_seconds": status.get("interval_seconds", 5),
                "session_records_saved": status.get("total_saved", 0),
                "total_measurements": total_measurements,
                "last_measurement": status.get("last_measurement"),
            }
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Unable to retrieve monitoring status."
        }), 500


@network_bp.route("/api/network/wifi", methods=["GET"])
def wifi_networks():
    """Return nearby Wi-Fi networks detected by this computer."""

    try:
        data = scan_wifi_networks()

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception:
        current_app.logger.exception("Wi-Fi scanning failed.")

        return jsonify({
            "success": False,
            "message": "Unable to scan nearby Wi-Fi networks."
        }), 503


from app.services.location_intelligence import (
    save_location_speed_test,
    find_best_nearby_spots,
)


@network_bp.route("/api/location/speed-tests", methods=["POST"])
def location_speed_test_submit():
    """Save a GPS-verified, user-measured speed test."""
    payload = request.get_json(silent=True) or {}

    try:
        record = save_location_speed_test(payload)
        return jsonify({
            "success": True,
            "message": "Location speed measurement saved.",
            "data": {
                "id": record.id,
                "created_at": record.created_at.isoformat(),
            }
        }), 201
    except ValueError as error:
        db.session.rollback()
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Location speed-test save failed.")
        return jsonify({
            "success": False,
            "message": "Unable to save the location speed test."
        }), 500


@network_bp.route("/api/location/best-spots", methods=["GET"])
def location_best_spots():
    """Find measured network-performance spots near GPS coordinates."""
    try:
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        radius = request.args.get("radius_km", default=3, type=float)

        if latitude is None or longitude is None:
            return jsonify({
                "success": False,
                "message": "Latitude and longitude are required."
            }), 400

        results = find_best_nearby_spots(latitude, longitude, radius)

        return jsonify({
            "success": True,
            "radius_km": radius,
            "total": len(results),
            "data": results,
            "message": (
                "Nearby measured locations found."
                if results else
                "No verified measurements are available in this area yet."
            )
        }), 200

    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception:
        current_app.logger.exception("Nearby location search failed.")
        return jsonify({
            "success": False,
            "message": "Unable to search nearby network locations."
        }), 500
