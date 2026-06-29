"""Composición de dependencias (composition root).

Ensambla: configuración, engine de DB, repositorios, casos de uso, rutas,
rate limiter, email sender y servicio TOTP.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from ..application.use_cases import (
    AppendChat,
    ClearChat,
    CreateCV,
    DeleteCV,
    DisableTotp,
    DuplicateCV,
    ForgotPassword,
    GetCV,
    GetChat,
    ListCVs,
    LoginUser,
    Logout,
    RefreshSession,
    RegenerateBackupCodes,
    RegisterUser,
    ResendVerification,
    ResetPassword,
    SetupTotpConfirm,
    SetupTotpStart,
    UpdateCV,
    VerifyEmail,
    VerifyTwoFactor,
)
from ..domain.repositories import (
    BackupCodeRepository,
    ChatRepository,
    CVRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    TwoFactorPendingRepository,
    UserRepository,
)
from ..infrastructure.auth.local_auth import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)
from ..infrastructure.email.sender import EmailSender, get_email_sender
from ..infrastructure.persistence.database import (
    create_all,
    get_db_url,
    get_session,
    is_postgres,
)
from ..infrastructure.persistence.sqlalchemy_backup_codes_repo import (
    SQLAlchemyBackupCodeRepository,
)
from ..infrastructure.persistence.sqlalchemy_chat_repo import SQLAlchemyChatRepository
from ..infrastructure.persistence.sqlalchemy_cv_repo import SQLAlchemyCVRepository
from ..infrastructure.persistence.sqlalchemy_email_verification_repo import (
    SQLAlchemyEmailVerificationTokenRepository,
)
from ..infrastructure.persistence.sqlalchemy_password_reset_repo import (
    SQLAlchemyPasswordResetTokenRepository,
)
from ..infrastructure.persistence.sqlalchemy_refresh_token_repo import (
    SQLAlchemyRefreshTokenRepository,
)
from ..infrastructure.persistence.sqlalchemy_two_factor_pending_repo import (
    SQLAlchemyTwoFactorPendingRepository,
)
from ..infrastructure.persistence.sqlalchemy_user_repo import SQLAlchemyUserRepository
from ..infrastructure.web.errors import register_error_handlers
from ..infrastructure.web.flask_app import create_flask_app
from ..infrastructure.web.limiter import register_limiter
from ..infrastructure.web.routes import register_routes, set_auth_callbacks

log = logging.getLogger(__name__)


@dataclass
class AppConfig:
    cors_origins: list[str]
    is_production: bool
    database_url: str
    secret_key: str
    frontend_url: str
    skip_email_verification: bool

    @classmethod
    def from_env(cls) -> "AppConfig":
        cors_raw = os.environ.get("CORS_ORIGINS", "*").strip()
        if cors_raw == "*":
            cors_list: list[str] = ["*"]
        else:
            cors_list = [o.strip() for o in cors_raw.split(",") if o.strip()] or ["*"]
        return cls(
            cors_origins=cors_list,
            is_production=os.environ.get("RAILWAY_ENVIRONMENT") == "production"
            or os.environ.get("FLASK_ENV") == "production",
            database_url=os.environ.get("DATABASE_URL", "").strip(),
            secret_key=os.environ.get("JWT_SECRET_KEY")
            or os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod"),
            frontend_url=os.environ.get("FRONTEND_URL", "http://localhost:5173").strip(),
            skip_email_verification=os.environ.get("CREATOR_CV_SKIP_EMAIL_VERIFICATION") == "1",
        )


def build_app():
    cfg = AppConfig.from_env()
    app = create_flask_app(cors_origins=cfg.cors_origins)
    app.config["SECRET_KEY"] = cfg.secret_key

    url = get_db_url()
    if is_postgres(url):
        log.info("DB: Postgres detectado, saltando create_all (usar Alembic)")
    elif os.environ.get("CREATOR_CV_ALLOW_SQLITE") == "1":
        log.warning(
            "DB: SQLite local (CREATOR_CV_ALLOW_SQLITE=1). Los tipos UUID/JSONB "
            "pueden no funcionar — usar Postgres/Neon en su lugar."
        )
        create_all()
    else:
        raise RuntimeError(
            "DATABASE_URL no configurada o apunta a SQLite. "
            "Este proyecto usa Postgres (Neon). "
            "Configurar DATABASE_URL con la connection string de Neon "
            "(ver backend/.env.example) y ejecutar `uv run alembic upgrade head`. "
            "Si necesitás SQLite para tests rápidos, setear CREATOR_CV_ALLOW_SQLITE=1."
        )

    register_limiter(app)

    # ── Repositorios ─────────────────────────────────────────────────
    user_repo: UserRepository = SQLAlchemyUserRepository()
    cv_repo: CVRepository = SQLAlchemyCVRepository()
    chat_repo: ChatRepository = SQLAlchemyChatRepository()
    email_verif_repo: EmailVerificationTokenRepository = (
        SQLAlchemyEmailVerificationTokenRepository()
    )
    pwd_reset_repo: PasswordResetTokenRepository = (
        SQLAlchemyPasswordResetTokenRepository()
    )
    refresh_repo: RefreshTokenRepository = SQLAlchemyRefreshTokenRepository()
    backup_repo: BackupCodeRepository = SQLAlchemyBackupCodeRepository()
    twofa_pending_repo: TwoFactorPendingRepository = (
        SQLAlchemyTwoFactorPendingRepository()
    )

    # ── Email sender ─────────────────────────────────────────────────
    email_sender: EmailSender = get_email_sender()

    # ── Callbacks de auth para las rutas ─────────────────────────────
    set_auth_callbacks(
        password_hasher=hash_password,
        token_creator=create_access_token,
        user_repo=user_repo,
        refresh_repo=refresh_repo,
    )

    # ── Casos de uso ─────────────────────────────────────────────────
    register_user_uc = RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url=cfg.frontend_url,
        skip_verification=cfg.skip_email_verification,
    )
    login_user_uc = LoginUser(
        user_repo, refresh_repo, twofa_pending_repo,
        password_verifier=verify_password,
        token_creator=create_access_token,
        require_verified=not cfg.skip_email_verification,
    )
    verify_email_uc = VerifyEmail(
        user_repo, email_verif_repo, refresh_repo, twofa_pending_repo,
        token_creator=create_access_token,
    )
    resend_verification_uc = ResendVerification(
        user_repo, email_verif_repo, email_sender,
        frontend_url=cfg.frontend_url,
    )
    forgot_password_uc = ForgotPassword(
        user_repo, pwd_reset_repo, refresh_repo, email_sender,
        frontend_url=cfg.frontend_url,
    )
    reset_password_uc = ResetPassword(
        user_repo, pwd_reset_repo, refresh_repo,
        password_hasher=hash_password,
    )
    refresh_session_uc = RefreshSession(
        user_repo, refresh_repo, token_creator=create_access_token,
    )
    logout_uc = Logout(refresh_repo)
    verify_two_factor_uc = VerifyTwoFactor(
        user_repo, twofa_pending_repo, backup_repo, refresh_repo,
        token_creator=create_access_token,
    )
    setup_totp_start_uc = SetupTotpStart(user_repo)
    setup_totp_confirm_uc = SetupTotpConfirm(user_repo, backup_repo)
    disable_totp_uc = DisableTotp(
        user_repo, backup_repo, password_verifier=verify_password
    )
    regenerate_backup_codes_uc = RegenerateBackupCodes(
        user_repo, backup_repo, password_verifier=verify_password
    )

    # ── Rutas ────────────────────────────────────────────────────────
    register_routes(
        app,
        create_cv=CreateCV(cv_repo),
        get_cv=GetCV(cv_repo),
        list_cvs=ListCVs(cv_repo),
        update_cv=UpdateCV(cv_repo),
        delete_cv=DeleteCV(cv_repo),
        duplicate_cv=DuplicateCV(cv_repo),
        get_chat=GetChat(chat_repo),
        append_chat=AppendChat(chat_repo),
        clear_chat=ClearChat(chat_repo),
        register_user=register_user_uc,
        login_user=login_user_uc,
        verify_email_uc=verify_email_uc,
        resend_verification_uc=resend_verification_uc,
        forgot_password_uc=forgot_password_uc,
        reset_password_uc=reset_password_uc,
        refresh_session_uc=refresh_session_uc,
        logout_uc=logout_uc,
        verify_two_factor_uc=verify_two_factor_uc,
        setup_totp_start_uc=setup_totp_start_uc,
        setup_totp_confirm_uc=setup_totp_confirm_uc,
        disable_totp_uc=disable_totp_uc,
        regenerate_backup_codes_uc=regenerate_backup_codes_uc,
        auth_verifier=verify_token,
    )

    register_error_handlers(app)
    return app
