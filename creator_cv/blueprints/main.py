from __future__ import annotations

import json

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select

from creator_cv.context_sync import (
    get_active_context_path,
    parse_cv_context_json,
    read_context_file,
    write_context_file,
)
from creator_cv.mcp_interview import (
    PendingInterviewError,
    append_to_review,
    apply_merge,
    collect_answers,
    get_pending_interview_path,
    get_review_markdown_path,
    pending_template_path,
    question_html,
    read_pending_file,
    remove_pending_file,
    seed_pending_from_template,
    validate_pending,
    write_review_file,
)
from creator_cv.cv_render import (
    context_has_preview_content,
    context_to_structured_preview_html,
    json_to_markdown,
    markdown_to_docx_bytes,
    markdown_to_pdf_bytes,
)
from creator_cv.extensions import db
from creator_cv.interview import (
    STEP_ORDER,
    apply_step,
    build_step_context,
    next_step_id,
    normalize_step,
    prev_step_id,
    step_index,
)
from creator_cv.models import CV, User

DEV_USER_EMAIL = "dev@local"

bp = Blueprint("main", __name__)


def get_dev_user() -> User:
    user = db.session.scalar(select(User).where(User.email == DEV_USER_EMAIL))
    if user is None:
        user = User(email=DEV_USER_EMAIL, password_hash=None)
        db.session.add(user)
        db.session.commit()
    return user


def _get_cv_or_404(cv_id: int, user: User) -> CV:
    cv = db.session.get(CV, cv_id)
    if cv is None or cv.user_id != user.id:
        abort(404)
    return cv


@bp.app_context_processor
def inject_mcp_path():
    app = current_app
    return {
        "mcp_context_path": str(get_active_context_path(app)),
        "mcp_interview_pending_path": str(get_pending_interview_path(app)),
    }


@bp.route("/")
def index():
    user = get_dev_user()
    cvs = db.session.scalars(
        select(CV).where(CV.user_id == user.id).order_by(CV.updated_at.desc())
    ).all()
    return render_template("index.html", cvs=cvs)


@bp.route("/cvs/new", methods=["POST"])
def cv_new():
    user = get_dev_user()
    title = (request.form.get("title") or "").strip() or "Sin título"
    cv = CV(user_id=user.id, title=title)
    db.session.add(cv)
    db.session.commit()
    flash("CV creado.", "success")
    return redirect(url_for("main.cv_edit", cv_id=cv.id))


@bp.route("/cvs/<int:cv_id>/interview/mcp", methods=["GET", "POST"])
def cv_interview_mcp(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    pending_path = get_pending_interview_path(current_app)
    review_path = get_review_markdown_path(current_app, cv.id)

    try:
        data = parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError) as e:
        flash(str(e), "error")
        return redirect(url_for("main.cv_edit", cv_id=cv.id))

    if request.method == "POST":
        raw = read_pending_file(pending_path)
        if raw is None:
            flash("No hay pregunta pendiente. Genera una en Cursor (archivo pending).", "error")
            return redirect(url_for("main.cv_interview_mcp", cv_id=cv.id))
        try:
            pending = validate_pending(raw, cv_id=cv.id)
            answers = collect_answers(pending, request.form)
            new_data = apply_merge(data, pending, answers)
            cv.context_json = json.dumps(new_data, ensure_ascii=False, indent=2)
            cv.review_markdown = append_to_review(cv.review_markdown, pending, answers)
            db.session.commit()
            write_review_file(review_path, cv.review_markdown or "")
            remove_pending_file(pending_path)
            flash(
                "Respuesta guardada. Contexto y revisión actualizados. "
                "La IA en Cursor puede leer el contexto y escribir la siguiente pregunta.",
                "success",
            )
        except PendingInterviewError as e:
            flash(str(e), "error")
        return redirect(url_for("main.cv_interview_mcp", cv_id=cv.id))

    raw: dict[str, Any] | None = None
    read_err: str | None = None
    try:
        raw = read_pending_file(pending_path)
    except PendingInterviewError as e:
        read_err = str(e)
    idle = raw is None and read_err is None
    pending_valid: dict[str, Any] | None = None
    err: str | None = read_err
    if raw is not None:
        try:
            pending_valid = validate_pending(raw, cv_id=cv.id)
            err = None
        except PendingInterviewError as e:
            err = str(e)
            pending_valid = None

    q_html = ""
    if pending_valid:
        q_html = question_html(pending_valid["question_markdown"])

    return render_template(
        "cv_interview_mcp.html",
        cv=cv,
        idle=idle,
        pending_error=err,
        pending=pending_valid,
        question_html_safe=q_html,
        template_path=str(pending_template_path()),
        review_path=str(review_path),
    )


@bp.route("/cvs/<int:cv_id>/interview/mcp/seed-template", methods=["POST"])
def cv_interview_mcp_seed_template(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    pending_path = get_pending_interview_path(current_app)
    try:
        existing = read_pending_file(pending_path)
    except PendingInterviewError as e:
        flash(
            f"No se puede crear un pending nuevo hasta corregir el archivo actual: {e}. "
            f"Ruta: {pending_path}",
            "error",
        )
        return redirect(url_for("main.cv_interview_mcp", cv_id=cv.id))
    if existing is not None:
        flash(
            "Ya existe un archivo pending con JSON válido. Respóndelo o bórralo antes "
            "de generar uno desde la plantilla.",
            "error",
        )
        return redirect(url_for("main.cv_interview_mcp", cv_id=cv.id))
    try:
        seed_pending_from_template(pending_path, cv_id=cv.id)
        flash(
            "Se creó cv-interview.pending.json desde la plantilla (primera pregunta de ejemplo). "
            "Puedes responder abajo; las siguientes rondas pueden seguir viniendo de Cursor/MCP.",
            "success",
        )
    except PendingInterviewError as e:
        flash(str(e), "error")
    except OSError as e:
        flash(str(e), "error")
    return redirect(url_for("main.cv_interview_mcp", cv_id=cv.id))


@bp.route("/cvs/<int:cv_id>/review")
def cv_review(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    md = (cv.review_markdown or "").strip()
    if not md:
        return render_template(
            "cv_review.html",
            cv=cv,
            review_html="",
            review_markdown="",
            review_empty=True,
        )
    html = question_html(md)
    return render_template(
        "cv_review.html",
        cv=cv,
        review_html=html,
        review_markdown=md,
        review_empty=False,
    )


@bp.route("/cvs/<int:cv_id>/interview", methods=["GET", "POST"])
def cv_interview(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    try:
        data = parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError) as e:
        flash(str(e), "error")
        return redirect(url_for("main.cv_edit", cv_id=cv.id))

    if request.method == "POST":
        step = normalize_step(request.form.get("step"))
        data = apply_step(step, request.form, data)
        cv.context_json = json.dumps(data, ensure_ascii=False, indent=2)
        db.session.commit()
        nxt = next_step_id(step)
        if nxt is None:
            flash("Entrevista completada. Puedes seguir editando el JSON a mano.", "success")
            return redirect(url_for("main.cv_edit", cv_id=cv.id))
        return redirect(url_for("main.cv_interview", cv_id=cv.id, step=nxt))

    step = normalize_step(request.args.get("step"))
    ctx = build_step_context(step, data)
    ctx["cv"] = cv
    ctx["step_num"] = step_index(step) + 1
    ctx["step_total"] = len(STEP_ORDER)
    ctx["prev_step"] = prev_step_id(step)
    return render_template("cv_interview.html", **ctx)


@bp.route("/cvs/<int:cv_id>/edit", methods=["GET", "POST"])
def cv_edit(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    if request.method == "POST":
        raw = request.form.get("context_json") or ""
        try:
            parse_cv_context_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            flash(str(e), "error")
            return render_template(
                "cv_edit.html",
                cv=cv,
                context_text=raw,
            ), 400
        cv.context_json = raw.strip() or None
        db.session.commit()
        flash("Contexto guardado en la base de datos.", "success")
        return redirect(url_for("main.cv_edit", cv_id=cv.id))

    text = cv.context_json or ""
    if not text.strip():
        text = json.dumps(
            read_context_file(get_active_context_path(current_app)),
            ensure_ascii=False,
            indent=2,
        )
    return render_template("cv_edit.html", cv=cv, context_text=text)


@bp.route("/cvs/<int:cv_id>/sync/from-mcp", methods=["POST"])
def cv_sync_from_mcp(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    path = get_active_context_path(current_app)
    try:
        data = read_context_file(path)
        cv.context_json = json.dumps(data, ensure_ascii=False, indent=2)
        db.session.commit()
        flash(f"Importado desde {path}", "success")
    except (OSError, json.JSONDecodeError, ValueError) as e:
        flash(str(e), "error")
    return redirect(url_for("main.cv_edit", cv_id=cv.id))


@bp.route("/cvs/<int:cv_id>/sync/to-mcp", methods=["POST"])
def cv_sync_to_mcp(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    path = get_active_context_path(current_app)
    try:
        if not cv.context_json or not cv.context_json.strip():
            flash("No hay contexto en BD para exportar. Guarda o importa primero.", "error")
            return redirect(url_for("main.cv_edit", cv_id=cv.id))
        data = parse_cv_context_json(cv.context_json)
        write_context_file(path, data)
        flash(f"Exportado a {path}", "success")
    except (OSError, ValueError) as e:
        flash(str(e), "error")
    return redirect(url_for("main.cv_edit", cv_id=cv.id))


@bp.route("/cvs/<int:cv_id>/preview")
def cv_preview(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    try:
        data = parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError) as e:
        flash(str(e), "error")
        return redirect(url_for("main.cv_edit", cv_id=cv.id))
    md = json_to_markdown(data)
    preview_html = context_to_structured_preview_html(data, fallback_title=cv.title)
    preview_empty = not context_has_preview_content(data)
    return render_template(
        "cv_preview.html",
        cv=cv,
        markdown=md,
        preview_html=preview_html,
        preview_empty=preview_empty,
    )


@bp.route("/cvs/<int:cv_id>/export.md")
def cv_export_md(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    try:
        data = parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError):
        abort(400)
    md = json_to_markdown(data)
    name = "".join(c if c.isalnum() or c in " -_" else "_" for c in cv.title) or "cv"
    return Response(
        md,
        mimetype="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{name.strip()[:80]}.md"'
        },
    )


@bp.route("/cvs/<int:cv_id>/export.pdf")
def cv_export_pdf(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    try:
        data = parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError):
        abort(400)
    md = json_to_markdown(data)
    try:
        pdf_bytes = markdown_to_pdf_bytes(md)
    except Exception:
        current_app.logger.exception("export_pdf")
        abort(500)
    name = "".join(c if c.isalnum() or c in " -_" else "_" for c in cv.title) or "cv"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{name.strip()[:80]}.pdf"'
        },
    )


@bp.route("/cvs/<int:cv_id>/export.docx")
def cv_export_docx(cv_id: int):
    user = get_dev_user()
    cv = _get_cv_or_404(cv_id, user)
    try:
        data = parse_cv_context_json(cv.context_json)
    except (json.JSONDecodeError, ValueError):
        abort(400)
    md = json_to_markdown(data)
    docx_bytes = markdown_to_docx_bytes(md)
    name = "".join(c if c.isalnum() or c in " -_" else "_" for c in cv.title) or "cv"
    return Response(
        docx_bytes,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{name.strip()[:80]}.docx"'
        },
    )
