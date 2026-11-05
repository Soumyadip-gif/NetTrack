import re
import subprocess
from datetime import datetime, timezone


def scan_wifi_networks():
    """Scan nearby Wi-Fi access points using Windows netsh."""

    result = subprocess.run(
        ["netsh", "wlan", "show", "networks", "mode=bssid"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("Windows Wi-Fi scan failed.")

    networks = []
    current_network = None
    current_access_point = None

    def finish_access_point():
        if current_network and current_access_point:
            current_network["access_points"].append(
                current_access_point.copy()
            )

    for line in result.stdout.splitlines():
        ssid_match = re.match(r"^\s*SSID\s+\d+\s*:\s*(.*)$", line)
        bssid_match = re.match(r"^\s*BSSID\s+\d+\s*:\s*(.*)$", line)

        if ssid_match:
            finish_access_point()

            if current_network:
                networks.append(current_network)

            current_network = {
                "ssid": ssid_match.group(1).strip() or "Hidden network",
                "network_type": "Unknown",
                "authentication": "Unknown",
                "encryption": "Unknown",
                "access_points": [],
            }
            current_access_point = None
            continue

        if current_network is None:
            continue

        if bssid_match:
            finish_access_point()
            current_access_point = {
                "bssid": bssid_match.group(1).strip(),
                "signal": None,
                "radio_type": "Unknown",
                "band": "Unknown",
                "channel": None,
            }
            continue

        value_match = re.match(r"^\s*([^:]+?)\s*:\s*(.*?)\s*$", line)

        if not value_match:
            continue

        key = value_match.group(1).strip().lower()
        value = value_match.group(2).strip()

        if current_access_point is None:
            if key == "network type":
                current_network["network_type"] = value
            elif key == "authentication":
                current_network["authentication"] = value
            elif key == "encryption":
                current_network["encryption"] = value
        else:
            if key == "signal":
                signal_match = re.search(r"\d+", value)
                if signal_match:
                    current_access_point["signal"] = int(
                        signal_match.group()
                    )
            elif key == "radio type":
                current_access_point["radio_type"] = value
            elif key == "band":
                current_access_point["band"] = value
            elif key == "channel":
                channel_match = re.search(r"\d+", value)
                if channel_match:
                    current_access_point["channel"] = int(
                        channel_match.group()
                    )

    finish_access_point()

    if current_network:
        networks.append(current_network)

    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "total_networks": len(networks),
        "total_access_points": sum(
            len(network["access_points"]) for network in networks
        ),
        "networks": networks,
    }
