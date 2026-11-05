
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    """Create and configure the NetTrack Flask application."""

    load_dotenv()

    app = Flask(__name__)

    # Application configuration
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "development-only-change-me"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///nettrack.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register database models
    from app import models

    # Register application blueprints
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)

    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.routes.network import network_bp
    app.register_blueprint(network_bp)

    return app
