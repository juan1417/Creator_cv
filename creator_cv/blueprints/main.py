"""Main blueprint — dashboard, CV CRUD, preview, export, AI adapt."""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Any

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import select
from werkzeug.datastructures import MultiDict

from .. import cv_render
from ..extensions import db
from ..form_parser import parse_form_to_cv
from ..match_scorer import score_match
from ..models import CV
from ..schemas import empty_cv, validate_cv
from ..cv_importer import (
    ALLOWED_EXTENSIONS,
    allowed_file,
    import_file_to_cv,
)

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)


# --- helpers ---


def _get_owned_cv(cv_id: int) -> CV:
    """Fetch a CV or 404 — and ensure it belongs to the current user."""
    cv = db.session.get(CV, cv_id)
    if cv is None or cv.user_id != current_user.id:
        abort(404)
    return cv


def _slug_from_name(name: str | None) -> str:
    if not name:
        return "cv"
    s = "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
    return s or "cv"


def _recompute_match(cv: CV) -> None:
    """Recompute the match score and persist it on ``cv`` (if there's an offer)."""
    import json as _json
    from datetime import datetime as _dt

    if not cv.job_offer or not cv.job_offer.strip():
        cv.match_score = None
        cv.match_summary = None
        cv.match_json = None
        cv.match_at = None
        return
    try:
        result = score_match(cv.context_dict(), cv.job_offer)
    except Exception:
        log.exception("score_match failed")
        return
    cv.match_score = int(result.get("total") or 0)
    cv.match_summary = result.get("summary") or ""
    cv.match_json = _json.dumps(result, ensure_ascii=False)
    cv.match_at = _dt.utcnow()


# --- Public landing ---


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


# --- Dashboard ---


@bp.route("/dashboard")
@login_required
def dashboard():
    cvs = list(
        db.session.scalars(
            select(CV).where(CV.user_id == current_user.id).order_by(CV.updated_at.desc())
        )
    )
    return render_template("dashboard.html", cvs=cvs)


# --- New CV ---


@bp.route("/cv/new", methods=("GET", "POST"))
@login_required
def cv_new():
    if request.method == "POST":
        form_data = request.form.to_dict(flat=False)
        flat = _flatten(form_data)
        try:
            cv_data = validate_cv(parse_form_to_cv(flat))
        except ValidationError as e:
            flash(f"Datos inválidos: {e.errors()[0]['msg']}", "error")
            return render_template("cv_form.html", cv=empty_cv(), job_offer="", cv_id=None)

        cv = CV(
            user_id=current_user.id,
            title=_derive_title(cv_data),
            job_offer=(request.form.get("job_offer") or "").strip() or None,
        )
        cv.set_context(cv_data)
        _recompute_match(cv)
        db.session.add(cv)
        db.session.commit()
        flash("CV creado.", "success")
        return redirect(url_for("main.cv_edit", cv_id=cv.id))
    return render_template("cv_form.html", cv=empty_cv(), job_offer="", cv_id=None)


# --- Improve CV (no job offer, generic upgrade) ---


@bp.route("/cv/<int:cv_id>/improve", methods=("POST",))
@login_required
def cv_improve(cv_id: int):
    """Reformulate the CV to be stronger in general (resumen, bullets, achievements, skills).

    Returns the new CV, the before/after match score (if there's a job offer
    attached), and a delta so the UI can show "+15 puntos".
    """
    from ..gemini_adapter import improve_cv, is_configured

    cv = _get_owned_cv(cv_id)
    if not is_configured():
        return _bad_request("La integración con IA no está configurada (GEMINI_API_KEY).")

    # Use current form data if present, otherwise the stored CV.
    flat = _flatten(request.form.to_dict(flat=False))
    base_cv = (
        parse_form_to_cv(flat)
        if any(k.startswith(("meta.", "experiencia")) for k in flat)
        else cv.context_dict()
    )

    # Score BEFORE the improvement (only if there's a job offer to score against).
    from ..match_scorer import score_match

    before_score: int | None = None
    before_meta: dict | None = None
    if cv.job_offer and cv.job_offer.strip():
        before_result = score_match(base_cv, cv.job_offer)
        before_score = int(before_result["total"])
        before_meta = {
            "tecnicas": before_result["dimensions"]["tecnicas"]["matched"],
            "idiomas": before_result["dimensions"]["idiomas"]["matched"],
        }

    try:
        improved_cv = improve_cv(base_cv)
    except RuntimeError as e:
        log.exception("Improve failed")
        return _bad_request(str(e))

    # Score AFTER (only if a job offer exists).
    after_score: int | None = None
    after_meta: dict | None = None
    if cv.job_offer and cv.job_offer.strip():
        after_result = score_match(improved_cv, cv.job_offer)
        after_score = int(after_result["total"])
        after_meta = {
            "tecnicas": after_result["dimensions"]["tecnicas"]["matched"],
            "idiomas": after_result["dimensions"]["idiomas"]["matched"],
        }

    delta: int | None = None
    if before_score is not None and after_score is not None:
        delta = after_score - before_score

    # Persist.
    cv.set_context(improved_cv)
    _recompute_match(cv)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "cv": improved_cv,
            "before_score": before_score,
            "after_score": after_score,
            "delta": delta,
            "before_meta": before_meta,
            "after_meta": after_meta,
        }
    )


# --- Import CV from file (PDF / DOCX) ---


@bp.route("/cv/import", methods=("GET", "POST"))
@login_required
def cv_import():
    from ..gemini_adapter import is_configured

    if request.method == "POST":
        upload = request.files.get("cv_file")
        if upload is None or not upload.filename:
            flash("Selecciona un archivo PDF o DOCX.", "warning")
            return redirect(url_for("main.cv_import"))
        if not allowed_file(upload.filename):
            flash(
                f"Tipo de archivo no soportado. Extensiones permitidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                "error",
            )
            return redirect(url_for("main.cv_import"))
        if not is_configured():
            flash(
                "Para importar un CV se necesita GEMINI_API_KEY configurada.",
                "error",
            )
            return redirect(url_for("main.cv_import"))

        try:
            cv_data = import_file_to_cv(upload)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("main.cv_import"))
        except RuntimeError as e:
            log.exception("Import failed")
            flash(str(e), "error")
            return redirect(url_for("main.cv_import"))

        cv = CV(
            user_id=current_user.id,
            title=_derive_title(cv_data),
            job_offer=None,
        )
        cv.set_context(cv_data)
        _recompute_match(cv)
        db.session.add(cv)
        db.session.commit()
        flash(
            "CV importado. Revisa los datos y ajústalo antes de adaptarlo a una oferta.",
            "success",
        )
        return redirect(url_for("main.cv_edit", cv_id=cv.id))

    return render_template(
        "cv_import.html",
        allowed_extensions=sorted(ALLOWED_EXTENSIONS),
        gemini_enabled=is_configured(),
    )


# --- Edit CV ---


@bp.route("/cv/<int:cv_id>")
@login_required
def cv_edit(cv_id: int):
    cv = _get_owned_cv(cv_id)
    return render_template(
        "cv_form.html",
        cv=cv.context_dict(),
        job_offer=cv.job_offer or "",
        review_md=cv.review_md or "",
        cv_id=cv.id,
    )


# --- Save CV (no AI) ---


@bp.route("/cv/<int:cv_id>/save", methods=("POST",))
@login_required
def cv_save(cv_id: int):
    cv = _get_owned_cv(cv_id)
    flat = _flatten(request.form.to_dict(flat=False))
    try:
        cv_data = validate_cv(parse_form_to_cv(flat))
    except ValidationError as e:
        return _bad_request(f"Datos inválidos: {e.errors()[0]['msg']}")

    cv.set_context(cv_data)
    cv.title = _derive_title(cv_data)
    cv.job_offer = (request.form.get("job_offer") or "").strip() or None
    _recompute_match(cv)
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "cv_id": cv.id,
            "title": cv.title,
            "match_score": cv.match_score,
            "match_summary": cv.match_summary,
        }
    )


# --- Adapt with Gemini (iterative, target score 70/100) ---


@bp.route("/cv/<int:cv_id>/adapt", methods=("POST",))
@login_required
def cv_adapt(cv_id: int):
    cv = _get_owned_cv(cv_id)
    job_offer = (request.form.get("job_offer") or "").strip()
    if not job_offer:
        return _bad_request("Pega una oferta de trabajo antes de adaptar con IA.")
    if len(job_offer) < 30:
        return _bad_request("La oferta es demasiado corta (mínimo 30 caracteres).")

    from ..gemini_adapter import adapt_until_score, is_configured

    if not is_configured():
        return _bad_request("La integración con IA no está configurada (GEMINI_API_KEY).")

    # Use the current form data if provided, otherwise the stored CV.
    flat = _flatten(request.form.to_dict(flat=False))
    base_cv = (
        parse_form_to_cv(flat)
        if any(k.startswith(("meta.", "experiencia")) for k in flat)
        else cv.context_dict()
    )

    # Configurable target / max iterations. Could be exposed in the UI later.
    target_score = 70
    max_iterations = 5

    try:
        adapted_cv, review_md, loop_meta = adapt_until_score(
            base_cv,
            job_offer,
            target_score=target_score,
            max_iterations=max_iterations,
        )
    except RuntimeError as e:
        log.exception("Gemini adapt failed")
        return _bad_request(str(e))

    cv.set_context(adapted_cv)
    cv.job_offer = job_offer
    cv.review_md = review_md
    _recompute_match(cv)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "cv": adapted_cv,
            "review_md": review_md,
            "match_score": cv.match_score,
            "match_summary": cv.match_summary,
            "loop": loop_meta,
        }
    )


# --- Preview ---


@bp.route("/cv/<int:cv_id>/preview")
@login_required
def cv_preview(cv_id: int):
    cv = _get_owned_cv(cv_id)
    return render_template("cv_preview.html", cv=cv.context_dict())


# --- Export PDF ---


@bp.route("/cv/<int:cv_id>/export.pdf")
@login_required
def cv_export_pdf(cv_id: int):
    cv = _get_owned_cv(cv_id)
    try:
        pdf_bytes = cv_render.render_pdf(cv.context_dict())
    except Exception:
        log.exception("PDF render failed")
        abort(500)
    filename = f"{_slug_from_name(cv.title)}-{cv.id}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Export DOCX ---


@bp.route("/cv/<int:cv_id>/export.docx")
@login_required
def cv_export_docx(cv_id: int):
    cv = _get_owned_cv(cv_id)
    try:
        docx_bytes = cv_render.render_docx(cv.context_dict())
    except Exception:
        log.exception("DOCX render failed")
        abort(500)
    filename = f"{_slug_from_name(cv.title)}-{cv.id}.docx"
    return Response(
        docx_bytes,
        mimetype=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Delete ---


@bp.route("/cv/<int:cv_id>/delete", methods=("POST",))
@login_required
def cv_delete(cv_id: int):
    cv = _get_owned_cv(cv_id)
    db.session.delete(cv)
    db.session.commit()
    flash("CV eliminado.", "info")
    return redirect(url_for("main.dashboard"))


# --- internals ---


def _flatten(md: MultiDict) -> dict[str, Any]:
    """Flask's ``request.form.to_dict(flat=False)`` returns lists for
    repeated keys. We collapse to single values (the form sends one
    per chip slot, but our regex parser walks them anyway)."""
    out: dict[str, Any] = {}
    for k, v in md.items():
        if isinstance(v, list):
            out[k] = v[0] if len(v) == 1 else v
        else:
            out[k] = v
    return out


def _derive_title(cv_data: dict) -> str:
    name = (cv_data.get("meta") or {}).get("nombre_completo") or ""
    title = (cv_data.get("meta") or {}).get("titulo_profesional") or ""
    base = name.strip() or title.strip()
    return f"CV de {base}" if base else "Mi CV"


def _bad_request(msg: str) -> Response:
    resp = jsonify({"ok": False, "error": msg})
    resp.status_code = 400
    return resp


# silence unused-import warnings
_ = (io, datetime)
