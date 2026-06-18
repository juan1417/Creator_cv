"""
Exporta los CVs de SQLite (app Flask actual) a un JSON que se puede
importar en la nueva versión estática con localStorage.

Uso:
    uv run python scripts/export_to_json.py > export-cvs.json
    uv run python scripts/export_to_json.py --output export-cvs.json
"""
import argparse
import json
import sys
from pathlib import Path

# Hacer accesibles los módulos de la app Flask
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from creator_cv import create_app  # noqa: E402
from creator_cv.models import CV, User  # noqa: E402
from creator_cv.context_sync import parse_cv_context_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", "-o", default="-", help="Archivo de salida (default: stdout)")
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        user = User.query.first()
        if not user:
            print("ERROR: no hay usuario en la DB.", file=sys.stderr)
            return 1

        cvs = CV.query.filter(CV.user_id == user.id).order_by(CV.created_at).all()
        out = {
            "version": 1,
            "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "cvs": [],
        }
        for cv in cvs:
            try:
                data = parse_cv_context_json(cv.context_json)
            except Exception:
                data = {}
            out["cvs"].append({
                "title": cv.title,
                "context_json": cv.context_json,
                "context": data,
                "created_at": cv.created_at.isoformat() if cv.created_at else None,
                "updated_at": cv.updated_at.isoformat() if cv.updated_at else None,
            })
        out["chat_history"] = []  # No hay chats en el modelo actual

        text = json.dumps(out, ensure_ascii=False, indent=2)
        if args.output == "-":
            print(text)
        else:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"Exportados {len(out['cvs'])} CV a {args.output}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
