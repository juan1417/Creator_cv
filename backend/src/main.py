"""Entry point: arranca el servidor Flask (gunicorn en producción, flask en dev).

Producción: gunicorn -w 2 -b 0.0.0.0:$PORT src.main:app
Desarrollo: python -m src.main
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

# Carga .env en desarrollo (Railway inyecta las vars directamente).
load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
)

from src.composition import build_app  # noqa: E402
from src.infrastructure.persistence.database import get_db_url, is_postgres  # noqa: E402

app = build_app()


def _log_db_info() -> None:
    url = get_db_url()
    if is_postgres(url):
        # No loggear credenciales: enmascarar password si aparece.
        safe = url
        for prefix in ("postgres://", "postgresql://", "postgresql+psycopg://"):
            if safe.startswith(prefix):
                tail = safe[len(prefix) :]
                if "@" in tail and ":" in tail[: tail.find("@")]:
                    user, rest = tail.split(":", 1)
                    safe = f"{prefix}{user}:***@{rest.split('@', 1)[1]}"
                break
        logging.getLogger(__name__).info("DB: Postgres → %s", safe)
    else:
        logging.getLogger(__name__).info("DB: SQLite local")


_log_db_info()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
