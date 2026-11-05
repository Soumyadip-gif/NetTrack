
import json
import os
import time

from pathlib import Path
from datetime import datetime, timezone

from app import create_app, db
from app.services.network_monitor import network_monitor


MONITOR_INTERVAL = 5

STATUS_FILE = (
    Path(__file__).resolve().parent
    / "instance"
    / "monitor_status.json"
)


def update_status(running, total_saved=0, last_measurement=None):
    """Write monitoring status atomically."""

    status = {
        "running": running,
        "pid": os.getpid(),
        "interval_seconds": MONITOR_INTERVAL,
        "total_saved": total_saved,
        "last_measurement": last_measurement,
    }

    temp_file = STATUS_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(status, indent=4))
    temp_file.replace(STATUS_FILE)


def run_monitor():
    app = create_app()
    total_saved = 0

    print("NetTrack background monitoring started.")
    print(f"Sampling interval: {MONITOR_INTERVAL} seconds")
    print("Press Ctrl+C to stop.\n")

    with app.app_context():

        network_monitor.get_network_stats()

        update_status(True)

        try:
            while True:
                time.sleep(MONITOR_INTERVAL)

                try:
                    stats = network_monitor.get_network_stats()
                    result = network_monitor.save_network_metrics(stats)

                    saved = result["saved_records"]
                    total_saved += saved

                    measurement_time = datetime.now(
                        timezone.utc
                    ).isoformat()

                    update_status(
                        True,
                        total_saved,
                        measurement_time
                    )

                    print(
                        f"Monitoring active | "
                        f"Records saved: {saved} | "
                        f"Total: {total_saved}"
                    )

                except Exception as error:
                    db.session.rollback()
                    print(f"Monitoring error: {error}")

        except KeyboardInterrupt:
            print("\nNetTrack monitoring stopped.")

        finally:
            update_status(False, total_saved)
            db.session.remove()


if __name__ == "__main__":
    run_monitor()
