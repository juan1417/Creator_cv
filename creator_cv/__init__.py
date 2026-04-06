import os

from dotenv import load_dotenv
from flask import Flask

from creator_cv.extensions import csrf, db, migrate

load_dotenv()


def _env_truthy(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name, "")
    if raw.strip() == "":
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off")


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    default_db = (
        os.environ.get("DATABASE_URL")
        or "sqlite:///creator_cv.sqlite3"
    )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-in-production"),
        SQLALCHEMY_DATABASE_URI=default_db,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CREATOR_CV_CONTEXT_PATH=os.environ.get("CREATOR_CV_CONTEXT_PATH", ""),
        CREATOR_CV_INTERVIEW_PENDING_PATH=os.environ.get(
            "CREATOR_CV_INTERVIEW_PENDING_PATH", ""
        ),
        CREATOR_CV_REVIEW_PATH=os.environ.get("CREATOR_CV_REVIEW_PATH", ""),
        CREATOR_CV_INTERVIEW_AUTO_FIRST_PENDING=_env_truthy(
            "CREATOR_CV_INTERVIEW_AUTO_FIRST_PENDING", True
        ),
    )

    if test_config is not None:
        app.config.update(test_config)

    if not app.config.get("CREATOR_CV_CONTEXT_PATH"):
        app.config["CREATOR_CV_CONTEXT_PATH"] = None
    if not app.config.get("CREATOR_CV_INTERVIEW_PENDING_PATH"):
        app.config["CREATOR_CV_INTERVIEW_PENDING_PATH"] = None
    if not app.config.get("CREATOR_CV_REVIEW_PATH"):
        app.config["CREATOR_CV_REVIEW_PATH"] = None

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from creator_cv import models  # noqa: F401

    from creator_cv.blueprints.main import bp as main_bp

    app.register_blueprint(main_bp)

    @app.after_request
    def _disable_cache_for_dynamic_pages(response):
        # Evita formularios/tokens viejos cuando hay varias recargas en dev.
        if not (response.cache_control and response.cache_control.public):
            if not str(response.mimetype or "").startswith(
                ("text/css", "application/javascript", "image/")
            ):
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        return response

    return app
