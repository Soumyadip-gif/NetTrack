from pathlib import Path

content = """# NetTrack

**Smart Network Monitoring and Location Intelligence System**

NetTrack is a Flask-based network monitoring dashboard designed to monitor network activity, inspect nearby Wi-Fi networks, and provide GPS-based location intelligence. It stores network measurements in SQLite and exposes APIs for dashboard data and location-based speed-test records.

> **Project status:** Active development. Mobile-network tracking and the Android companion application are planned features, not yet implemented.

## Features

### Current implementation

- **Network monitoring**
  - Detects available network interfaces.
  - Tracks upload and download traffic.
  - Stores historical network metrics.
  - Provides network statistics and history APIs.

- **Wi-Fi scanning**
  - Scans nearby Wi-Fi networks on supported Windows systems using `netsh`.
  - Displays discovered network information in the dashboard.
  - Scanning is read-only; NetTrack does not connect to networks or retrieve Wi-Fi passwords.

- **GPS location intelligence**
  - Uses the browser's geolocation permission to obtain the device's location.
  - Displays coordinates and reported location accuracy.
  - Shows the location on an interactive Leaflet map.

- **Location-based speed-test data**
  - Provides an API for submitting GPS-tagged speed-test measurements.
  - Stores location, download/upload speed, ping, jitter, provider, connection type and measurement metadata.
  - Includes an initial nearby-measurement lookup and ranking service.

- **Application health**
  - Provides a health-check API.
  - Uses SQLite through Flask-SQLAlchemy.
  - Includes database migrations through Flask-Migrate.

### Planned features

- Android companion application.
- Tracking only the SIM currently inserted in the Android phone.
- Cellular operator, network type and signal-strength monitoring.
- Cell and tower information where Android and the device permit access.
- Mobile internet speed tests with GPS-tagged results.
- Signal-strength and internet-performance coverage maps.
- Signal and speed heatmaps.
- Improved nearby-location recommendations based on real measurements.

Planned features should not be interpreted as currently available functionality.

## Technology stack

- **Backend:** Python, Flask
- **Database:** SQLite, Flask-SQLAlchemy
- **Database migrations:** Flask-Migrate, Alembic
- **Frontend:** HTML, CSS, JavaScript
- **Maps:** Leaflet
- **Network monitoring:** psutil
- **Wi-Fi scanning:** Windows `netsh`
- **Testing:** pytest

## Project structure

```text
NetTrack/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   └── __init__.py
├── config/
├── migrations/
├── tests/
├── .env.example
├── .gitignore
├── monitor_worker.py
├── pytest.ini
├── requirements.txt
└── run.py
```

## Requirements

- Python 3.13 or a compatible Python version.
- Windows is required for the current `netsh`-based Wi-Fi scanner.
- Git.
- A modern web browser.
- Internet access for loading map assets and tiles.

## Setup on Windows

### 1. Clone the repository

```powershell
git clone https://github.com/Soumyadip-gif/NetTrack.git
cd NetTrack
```

### 2. Create and activate a virtual environment

```powershell
py -3.13 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

If Python 3.13 is not installed, use an installed compatible Python version.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set a strong, private `SECRET_KEY`. Keep `.env` out of Git. The example configuration uses SQLite:

```dotenv
SECRET_KEY=replace-with-a-secure-secret
DATABASE_URL=sqlite:///nettrack.db
```

### 5. Apply database migrations

```powershell
flask --app run.py db upgrade
```

### 6. Start the application

```powershell
python run.py
```

Open the dashboard at:

http://127.0.0.1:5000

## Running tests

From the project directory with the virtual environment activated:

```powershell
pytest -q
```

## API endpoints

The current application includes these routes:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Network dashboard |
| GET | `/api/health` | Application health check |
| GET | `/api/network/stats` | Current network statistics |
| GET | `/api/network/history` | Historical network metrics |
| GET | `/api/network/status` | Monitoring status |
| GET | `/api/network/wifi` | Nearby Wi-Fi scan results |
| POST | `/api/location/speed-tests` | Submit a location-based speed-test measurement |
| GET | `/api/location/best-spots` | Find nearby saved measurement locations |

Location endpoints require valid coordinates and measurement data. See the route and service implementation for validation details.

## Privacy and permissions

- Browser GPS access requires the user's permission.
- Location and speed-test data submitted to the application may be stored in its local database.
- Do not commit `.env`, database files, personal location data, or other secrets.
- The current laptop-based network monitor measures the laptop's active network connection. It does not directly read cellular signal strength from a SIM.
- Direct SIM and cellular radio monitoring is planned through a future Android companion application and will depend on Android permissions and device support.

## Current limitations

- The current Wi-Fi scanner uses Windows-specific `netsh` commands.
- Browser geolocation accuracy depends on the device, browser and permission settings.
- Nearby-spot rankings are based on saved measurements; a location without measurements cannot be assumed to have good network performance.
- The current location-speed-test API stores submitted measurements; a complete automated speed-test workflow is still under development.
- Cellular signal tracking, SIM monitoring and mobile coverage heatmaps are planned, not yet implemented.

## Contributing

This project is under active development. Before making changes:

1. Create a feature branch.
2. Keep secrets and local databases out of commits.
3. Run the test suite.
4. Submit changes with a clear commit message.

## License

No license has been added yet. Unless a license is added to this repository, standard copyright restrictions apply.
"""
path = Path("/mnt/data/README.md")
path.write_text(content, encoding="utf-8")
print(f"Created {path} ({path.stat().st_size} bytes)")
