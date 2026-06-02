"""Auth blueprint — registration, login, logout."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


# --- Tiny form helpers (no Flask-WTF declarative forms to keep things simple) ---


class RegisterForm:
    def __init__(self, data: dict) -> None:
        self.errors: dict[str, str] = {}
        self.email = (data.get("email") or "").strip().lower()
        self.password = data.get("password") or ""
        self.password_confirm = data.get("password_confirm") or ""
        self.full_name = (data.get("full_name") or "").strip() or None

    def validate(self) -> bool:
        if not self.email or "@" not in self.email:
            self.errors["email"] = "Email inválido."
        if len(self.password) < 8:
            self.errors["password"] = "La contraseña debe tener al menos 8 caracteres."
        if self.password != self.password_confirm:
            self.errors["password_confirm"] = "Las contraseñas no coinciden."
        return not self.errors


class LoginForm:
    def __init__(self, data: dict) -> None:
        self.errors: dict[str, str] = {}
        self.email = (data.get("email") or "").strip().lower()
        self.password = data.get("password") or ""

    def validate(self) -> bool:
        if not self.email or "@" not in self.email:
            self.errors["email"] = "Email inválido."
        if not self.password:
            self.errors["password"] = "Contraseña requerida."
        return not self.errors


# --- Routes ---


@bp.route("/register", methods=("GET", "POST"))
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm(request.form if request.method == "POST" else {})
    if request.method == "POST" and form.validate():
        user = User(email=form.email, full_name=form.full_name)
        user.set_password(form.password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.errors["email"] = "Ese email ya está registrado."
        else:
            login_user(user)
            flash("Cuenta creada. Bienvenido/a.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm(request.form if request.method == "POST" else {})
    if request.method == "POST" and form.validate():
        user = db.session.scalar(select(User).where(User.email == form.email))
        if user is None or not user.check_password(form.password):
            form.errors["password"] = "Credenciales inválidas."
        else:
            login_user(user)
            flash("Sesión iniciada.", "success")
            next_url = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_url)
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.index"))
