import time
import socket
import psutil
from app import db
from app.models import NetworkMetric


class NetworkMonitor:
    """Collect real-time network interface and traffic statistics."""

    def __init__(self):
        self.previous_stats = None
        self.previous_time = None

    def get_network_stats(self):
        """Return network traffic statistics and interface information."""

        current_time = time.monotonic()
        current_stats = psutil.net_io_counters(pernic=True)

        interfaces = psutil.net_if_stats()
        addresses = psutil.net_if_addrs()

        results = []

        for interface, stats in current_stats.items():
            previous = (
                self.previous_stats.get(interface)
                if self.previous_stats else None
            )

            download_mbps = 0.0
            upload_mbps = 0.0

            if previous and self.previous_time is not None:
                elapsed = current_time - self.previous_time

                if elapsed > 0:
                    download_mbps = (
                        (stats.bytes_recv - previous.bytes_recv)
                        * 8 / elapsed / 1_000_000
                    )

                    upload_mbps = (
                        (stats.bytes_sent - previous.bytes_sent)
                        * 8 / elapsed / 1_000_000
                    )

            interface_info = interfaces.get(interface)

            ip_addresses = [
                address.address
                for address in addresses.get(interface, [])
                if address.family == socket.AF_INET
            ]

            results.append({
                "interface": interface,
                "is_up": interface_info.isup if interface_info else False,
                "speed_mbps": (
                    interface_info.speed if interface_info else 0
                ),
                "ip_addresses": ip_addresses,
                "bytes_received": stats.bytes_recv,
                "bytes_sent": stats.bytes_sent,
                "download_mbps": round(max(0, download_mbps), 3),
                "upload_mbps": round(max(0, upload_mbps), 3),
            })

        self.previous_stats = current_stats
        self.previous_time = current_time

        return {
            "timestamp": time.time(),
            "interfaces": results,
        }

    def save_network_metrics(self, stats_data):
        """Save measured traffic speeds for active interfaces."""

        records = []

        try:
            for item in stats_data["interfaces"]:

                if not item["is_up"]:
                    continue

                if "loopback" in item["interface"].lower():
                    continue

                record = NetworkMetric(
                    interface=item["interface"],
                    download_speed=item["download_mbps"],
                    upload_speed=item["upload_mbps"],
                )

                db.session.add(record)
                records.append(record)

            db.session.commit()

            return {
                "success": True,
                "saved_records": len(records),
            }

        except Exception:
            db.session.rollback()
            raise


# Shared monitor instance
network_monitor = NetworkMonitor()
