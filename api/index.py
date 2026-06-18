"""
Vercel serverless function: expone el Flask app como WSGI handler.

Vercel enruta /api/* a esta función. Flask maneja el routing interno.

Uso:
    vercel.json debe tener un rewrite:
        { "source": "/api/(.*)", "destination": "/api/index.py" }
    o equivalente.

Nota: NO importamos creator_cv arriba del todo para que los errores
de import no rompan el cold start.
"""
import os
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto está en sys.path
# (Vercel suele setear esto automáticamente, pero por las dudas)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Cargar .env si existe (Vercel no usa .env, pero por si se deploya local)
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

# Inicializar Flask app
from creator_cv import create_app  # noqa: E402

app = create_app()


# Vercel Python runtime espera una variable `app` o un handler `handler`.
# Como Flask es WSGI, usamos vercel-wsgi o un adapter manual.
# Esto evita agregar dependencia: hacemos un adapter mínimo.
def handler(request, context):
    """
    Adapter WSGI mínimo para Vercel Python runtime.

    Vercel envía un dict con keys: method, path, headers, body, query.
    Devolvemos un dict con statusCode, headers, body.
    """
    import io
    from werkzeug.datastructures import EnvironBuilder
    from werkzeug.wrappers import Request, Response

    # Construir environ WSGI desde el request de Vercel
    method = request.get("method", "GET")
    path = request.get("path", "/")
    query = request.get("query", {}) or {}
    headers = request.get("headers", {}) or {}
    body = request.get("body", b"") or b""

    # Construir querystring
    qs = "&".join(f"{k}={v}" for k, v in query.items()) if isinstance(query, dict) else str(query)
    if not qs and "?" in path:
        qs = path.split("?", 1)[1]
        path = path.split("?", 1)[0]

    # Headers como tuplas
    header_list = []
    for k, v in headers.items():
        if isinstance(v, list):
            for vv in v:
                header_list.append((k.lower(), vv))
        else:
            header_list.append((k.lower(), str(v)))

    environ = {
        "REQUEST_METHOD": method,
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": qs,
        "SERVER_NAME": "vercel",
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(body if isinstance(body, bytes) else body.encode("utf-8")),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "wsgi.version": (1, 0),
        "CONTENT_TYPE": headers.get("content-type", headers.get("Content-Type", "")),
        "CONTENT_LENGTH": str(len(body) if body else 0),
    }
    for k, v in header_list:
        key = "HTTP_" + k.upper().replace("-", "_")
        environ[key] = v

    # Llamar al Flask app
    response_data = {}

    def start_response(status, response_headers, exc_info=None):
        response_data["status"] = status
        response_data["headers"] = response_headers

    body_iter = app.wsgi_app(environ, start_response)
    response_body = b"".join(body_iter)

    # Parsear status code
    status_code = int(response_data.get("status", "200 OK").split(" ", 1)[0])

    return {
        "statusCode": status_code,
        "headers": dict(response_data.get("headers", [])),
        "body": response_body.decode("utf-8", errors="replace"),
    }
