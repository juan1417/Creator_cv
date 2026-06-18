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


def _normalize_db_url(url: str) -> str:
    """SQLAlchemy necesita postgresql:// (no postgres://) y ssl para Supabase."""
    if not url:
        return url
    # Heroku/Supabase/Railway suelen dar postgres://; SQLAlchemy quiere postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    # Supabase requiere sslmode=require en producción
    if "postgresql" in url and "sslmode=" not in url and "supabase" in url.lower():
        sep = "&" if "?" in url else "?"
        url = url + sep + "sslmode=require"
    return url


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    is_production = os.environ.get("VERCEL_ENV") == "production" or os.environ.get("FLASK_ENV") == "production"

    default_db = (
        os.environ.get("DATABASE_URL")
        or "sqlite:///creator_cv.sqlite3"
    )
    default_db = _normalize_db_url(default_db)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key and is_production:
        raise RuntimeError(
            "SECRET_KEY es obligatorio en producción. "
            "Configurá una clave aleatoria en Vercel → Environment Variables."
        )
    if not secret_key:
        secret_key = "dev-only-not-for-production"

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=default_db,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CREATOR_CV_CONTEXT_PATH=None,  # en Vercel no hay filesystem
        CREATOR_CV_INTERVIEW_PENDING_PATH=None,
        CREATOR_CV_REVIEW_PATH=None,
        CREATOR_CV_INTERVIEW_AUTO_FIRST_PENDING=False,  # MCP no funciona sin filesystem
    )

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    # Migrate solo se usa en local; en Vercel las tablas se crean con create_all()
    if not is_production:
        migrate.init_app(app, db)
    csrf.init_app(app)

    from creator_cv import models  # noqa: F401

    from creator_cv.blueprints.main import bp as main_bp
    from creator_cv.blueprints.api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Crear tablas en Vercel (donde no hay Alembic migrations)
    if is_production:
        with app.app_context():
            db.create_all()

    @app.after_request
    def _disable_cache_for_dynamic_pages(response):
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
