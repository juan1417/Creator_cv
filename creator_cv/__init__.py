import os

from dotenv import load_dotenv
from flask import Flask

from creator_cv.extensions import csrf, db, migrate

load_dotenv()


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

    return app
