"""Creator CV — Flask application factory.

Use ``flask --app app:create_app run`` to start the dev server.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from .config import get_config
from .extensions import csrf, db, login_manager, migrate


def create_app() -> Flask:
    """Build and configure the Flask app."""
    app = Flask(
        __name__,
        instance_path=str(Path(__file__).resolve().parent.parent / "instance"),
        instance_relative_config=False,
    )
    app.config.from_object(get_config())

    # Ensure the instance directory exists (SQLite target).
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _register_extensions(app)
    _register_blueprints(app)
    _register_user_loader()
    _register_context(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from .blueprints.auth import bp as auth_bp
    from .blueprints.main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)


def _register_user_loader() -> None:
    # Import inside the function to avoid circular imports at module load.
    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))


def _register_context(app: Flask) -> None:
    from .gemini_adapter import is_configured as gemini_is_configured
    from .match_scorer import badge_color

    @app.context_processor
    def inject_globals() -> dict:
        return {
            "app_name": app.config["APP_NAME"],
            "gemini_enabled": gemini_is_configured(),
        }

    @app.template_filter("match_badge_class")
    def _match_badge_class_filter(score):
        if score is None:
            return "badge-gray"
        return badge_color(int(score))
