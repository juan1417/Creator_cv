"""Entry point: arranca el servidor Flask (gunicorn en producción, flask en dev).

Producción: gunicorn -w 2 -b 0.0.0.0:$PORT src.main:app
Desarrollo: python -m src.main
"""
import os

from dotenv import load_dotenv

# Carga .env en desarrollo (Railway inyecta las vars directamente)
load_dotenv()

from src.composition import build_app  # noqa: E402

app = build_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
