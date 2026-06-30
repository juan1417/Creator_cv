"""Tests unitarios de los use cases con repositorios en memoria."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Sequence

import pytest

from src.application.use_cases import (
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
from src.infrastructure.auth import totp as totp_svc
from src.application.inputs import (
    CreateCVInput,
    DeleteCVInput,
    GetCVInput,
    ListCVsInput,
    UpdateCVInput,
)
from src.domain.entities import (
    CV,
    BackupCode,
    ChatMessage,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    TwoFactorPending,
    User,
)
from src.domain.exceptions import (
    CVNotFoundError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    RefreshTokenReuseDetectedError,
    TokenExpiredError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserAlreadyExistsError,
    ValidationError,
)
from src.domain.repositories import (
    BackupCodeRepository,
    CVRepository,
    ChatRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    TwoFactorPendingRepository,
    UserRepository,
)
from src.infrastructure.auth.tokens import generate_token, hash_token


# ── In-memory repos ──────────────────────────────────────────────────────


class InMemoryCVRepo(CVRepository):
    def __init__(self) -> None:
        self._items: dict[str, CV] = {}

    def create(self, cv: CV) -> CV:
        cv.id = f"cv-{len(self._items) + 1}"
        self._items[cv.id] = cv
        return cv

    def get(self, cv_id: str, user_id: str) -> CV:
        cv = self._items.get(cv_id)
        if not cv or cv.user_id != user_id:
            raise CVNotFoundError(cv_id)
        return cv

    def list_for_user(self, user_id: str) -> Sequence[CV]:
        return [cv for cv in self._items.values() if cv.user_id == user_id]

    def update(self, cv: CV) -> CV:
        self._items[cv.id] = cv
        return cv

    def delete(self, cv_id: str, user_id: str) -> None:
        cv = self.get(cv_id, user_id)
        del self._items[cv_id]


class InMemoryChatRepo(ChatRepository):
    def __init__(self) -> None:
        self._items: dict[str, list[ChatMessage]] = {}

    def get_messages(self, cv_id: str, user_id: str) -> list[ChatMessage]:
        return list(self._items.get(cv_id, []))

    def append(self, cv_id: str, user_id: str, message: ChatMessage) -> None:
        self._items.setdefault(cv_id, []).append(message)

    def clear(self, cv_id: str, user_id: str) -> None:
        self._items[cv_id] = []


class InMemoryUserRepo(UserRepository):
    def __init__(self) -> None:
        self._items: dict[str, User] = {}

    def get_by_id(self, user_id: str) -> User | None:
        return self._items.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        for u in self._items.values():
            if u.email == normalized:
                return u
        return None

    def create(self, user: User) -> User:
        if self.get_by_email(user.email) is not None:
            raise UserAlreadyExistsError(user.email)
        if not user.id:
            user.id = f"user-{uuid.uuid4().hex[:8]}"
        self._items[user.id] = user
        return user

    def update(self, user: User) -> User:
        if user.id not in self._items:
            raise UserAlreadyExistsError(user.email)
        self._items[user.id] = user
        return user


class InMemoryEmailVerificationTokenRepo(EmailVerificationTokenRepository):
    def __init__(self) -> None:
        self._items: dict[str, EmailVerificationToken] = {}

    def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        self._items[token.id] = token
        return token

    def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        for t in self._items.values():
            if t.token_hash == token_hash:
                return t
        return None

    def delete(self, token_id: str) -> None:
        self._items.pop(token_id, None)

    def delete_for_user(self, user_id: str) -> int:
        before = len(self._items)
        self._items = {
            tid: t for tid, t in self._items.items() if t.user_id != user_id
        }
        return before - len(self._items)


class InMemoryPasswordResetTokenRepo(PasswordResetTokenRepository):
    def __init__(self) -> None:
        self._items: dict[str, PasswordResetToken] = {}

    def create(self, token: PasswordResetToken) -> PasswordResetToken:
        self._items[token.id] = token
        return token

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        for t in self._items.values():
            if t.token_hash == token_hash:
                return t
        return None

    def delete(self, token_id: str) -> None:
        self._items.pop(token_id, None)

    def delete_for_user(self, user_id: str) -> int:
        before = len(self._items)
        self._items = {
            tid: t for tid, t in self._items.items() if t.user_id != user_id
        }
        return before - len(self._items)


class InMemoryRefreshTokenRepo(RefreshTokenRepository):
    def __init__(self) -> None:
        self._items: dict[str, RefreshToken] = {}

    def create(self, token: RefreshToken) -> RefreshToken:
        self._items[token.id] = token
        return token

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        for t in self._items.values():
            if t.token_hash == token_hash:
                return t
        return None

    def mark_revoked(
        self, token_id: str, replaced_by_id: str | None = None
    ) -> None:
        if token_id in self._items:
            self._items[token_id].revoked_at = datetime.now(timezone.utc)
            if replaced_by_id:
                self._items[token_id].replaced_by_id = replaced_by_id

    def revoke_family(self, family_id: str) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        for t in self._items.values():
            if t.family_id == family_id and t.revoked_at is None:
                t.revoked_at = now
                count += 1
        return count

    def revoke_all_for_user(self, user_id: str) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        for t in self._items.values():
            if t.user_id == user_id and t.revoked_at is None:
                t.revoked_at = now
                count += 1
        return count


class InMemoryBackupCodeRepo(BackupCodeRepository):
    def __init__(self) -> None:
        self._items: dict[str, BackupCode] = {}

    def create_many(self, codes: list[BackupCode]) -> list[BackupCode]:
        for c in codes:
            self._items[c.id] = c
        return codes

    def list_for_user(self, user_id: str) -> list[BackupCode]:
        return [c for c in self._items.values() if c.user_id == user_id]

    def get_by_hash(self, user_id: str, code_hash: str) -> BackupCode | None:
        for c in self._items.values():
            if c.user_id == user_id and c.code_hash == code_hash:
                return c
        return None

    def mark_used(self, code_id: str) -> None:
        if code_id in self._items:
            self._items[code_id].used_at = datetime.now(timezone.utc)

    def delete_all_for_user(self, user_id: str) -> int:
        before = len(self._items)
        self._items = {
            cid: c for cid, c in self._items.items() if c.user_id != user_id
        }
        return before - len(self._items)


class InMemoryTwoFactorPendingRepo(TwoFactorPendingRepository):
    def __init__(self) -> None:
        self._items: dict[str, TwoFactorPending] = {}

    def create(self, pending: TwoFactorPending) -> TwoFactorPending:
        self._items[pending.id] = pending
        return pending

    def get_by_hash(self, token_hash: str) -> TwoFactorPending | None:
        for p in self._items.values():
            if p.token_hash == token_hash:
                return p
        return None

    def delete(self, pending_id: str) -> None:
        self._items.pop(pending_id, None)

    def delete_for_user(self, user_id: str) -> int:
        before = len(self._items)
        self._items = {
            pid: p for pid, p in self._items.items() if p.user_id != user_id
        }
        return before - len(self._items)


@dataclass
class SentEmail:
    to: str
    subject: str
    html: str
    text: str


@dataclass
class FakeEmailSender:
    sent: list[SentEmail] = field(default_factory=list)

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        self.sent.append(SentEmail(to=to, subject=subject, html=html, text=text))


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def cv_repo():
    return InMemoryCVRepo()


@pytest.fixture
def chat_repo():
    return InMemoryChatRepo()


@pytest.fixture
def user_repo():
    return InMemoryUserRepo()


@pytest.fixture
def email_verif_repo():
    return InMemoryEmailVerificationTokenRepo()


@pytest.fixture
def pwd_reset_repo():
    return InMemoryPasswordResetTokenRepo()


@pytest.fixture
def refresh_repo():
    return InMemoryRefreshTokenRepo()


@pytest.fixture
def backup_repo():
    return InMemoryBackupCodeRepo()


@pytest.fixture
def twofa_pending_repo():
    return InMemoryTwoFactorPendingRepo()


@pytest.fixture
def email_sender():
    return FakeEmailSender()


# Encryption key para tests de 2FA — Fernet requiere url-safe base64 de 32 bytes.
@pytest.fixture(autouse=True)
def _set_encryption_key(monkeypatch):
    from cryptography.fernet import Fernet

    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))


def _password_hasher(p: str) -> str:
    return f"hashed::{p}"


def _password_verifier(p: str, h: str) -> bool:
    return h == f"hashed::{p}"


def _token_creator(user_id: str, email: str) -> str:
    """Mock que incluye timestamp-ish único via uuid para distinguir tokens."""
    return f"jwt::{user_id}::{email}::{uuid.uuid4().hex[:6]}"


def _register_verified(user_repo, email_verif_repo, email_sender, email="foo@example.com"):
    """Helper: registra un user verificado."""
    return RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://x", skip_verification=True,
    ).execute(email, "secret123", _password_hasher)


def _make_login(user_repo, refresh_repo, twofa_pending_repo, require_verified=True):
    return LoginUser(
        user_repo, refresh_repo, twofa_pending_repo,
        password_verifier=_password_verifier,
        token_creator=_token_creator,
        require_verified=require_verified,
    )


# ── CV / chat tests ──────────────────────────────────────────────────────


def test_create_cv_with_empty_context(cv_repo):
    use_case = CreateCV(cv_repo)
    result = use_case.execute("user-1", CreateCVInput(title="Mi CV"))
    assert result.id == "cv-1"
    assert result.title == "Mi CV"
    assert "meta" in result.context_json


def test_create_cv_strips_title(cv_repo):
    use_case = CreateCV(cv_repo)
    result = use_case.execute("user-1", CreateCVInput(title="  Hola  "))
    assert result.title == "Hola"


def test_create_cv_rejects_empty_title(cv_repo):
    use_case = CreateCV(cv_repo)
    with pytest.raises(ValidationError):
        use_case.execute("user-1", CreateCVInput(title="   "))


def test_list_cvs_filters_by_user(cv_repo):
    CreateCV(cv_repo).execute("user-1", CreateCVInput(title="A"))
    CreateCV(cv_repo).execute("user-1", CreateCVInput(title="B"))
    CreateCV(cv_repo).execute("user-2", CreateCVInput(title="C"))

    result = ListCVs(cv_repo).execute("user-1", ListCVsInput())
    assert len(result) == 2
    titles = {c.title for c in result}
    assert titles == {"A", "B"}


def test_update_cv_title(cv_repo):
    create = CreateCV(cv_repo)
    update = UpdateCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="Original"))
    updated = update.execute("user-1", UpdateCVInput(cv_id=cv.id, title="Nuevo"))
    assert updated.title == "Nuevo"


def test_update_cv_rejects_invalid_json(cv_repo):
    create = CreateCV(cv_repo)
    update = UpdateCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="X"))
    with pytest.raises(ValidationError):
        update.execute("user-1", UpdateCVInput(cv_id=cv.id, context_json="not json"))


def test_get_cv_from_other_user_raises(cv_repo):
    create = CreateCV(cv_repo)
    get = GetCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="X"))
    with pytest.raises(CVNotFoundError):
        get.execute("user-2", GetCVInput(cv_id=cv.id))


def test_delete_cv(cv_repo):
    create = CreateCV(cv_repo)
    delete = DeleteCV(cv_repo)
    cv = create.execute("user-1", CreateCVInput(title="X"))
    delete.execute("user-1", DeleteCVInput(cv_id=cv.id))
    with pytest.raises(CVNotFoundError):
        GetCV(cv_repo).execute("user-1", GetCVInput(cv_id=cv.id))


def test_duplicate_cv_creates_copy_with_copia_suffix(cv_repo):
    create = CreateCV(cv_repo)
    dup = DuplicateCV(cv_repo)
    original = create.execute("user-1", CreateCVInput(title="Senior Dev"))

    copy = dup.execute("user-1", original.id)

    assert copy.id != original.id
    assert copy.title == "Senior Dev (Copia)"
    assert copy.context_json == original.context_json
    # El original sigue existiendo
    ListCVs(cv_repo).execute("user-1", ListCVsInput())


def test_duplicate_cv_rejects_other_users_cv(cv_repo):
    create = CreateCV(cv_repo)
    dup = DuplicateCV(cv_repo)
    original = create.execute("user-1", CreateCVInput(title="Privado"))

    with pytest.raises(CVNotFoundError):
        dup.execute("user-2", original.id)


def test_chat_append_and_get(chat_repo):
    append = AppendChat(chat_repo)
    get = GetChat(chat_repo)
    append.execute("user-1", "cv-1", "user", "Hola", None)
    append.execute("user-1", "cv-1", "assistant", "Hola, ¿en qué te ayudo?", None)
    msgs = get.execute("user-1", "cv-1")
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"


def test_chat_clear(chat_repo):
    append = AppendChat(chat_repo)
    clear = ClearChat(chat_repo)
    get = GetChat(chat_repo)
    append.execute("user-1", "cv-1", "user", "Hola", None)
    clear.execute("user-1", "cv-1")
    assert get.execute("user-1", "cv-1") == []


# ── Auth tests ────────────────────────────────────────────────────────────


def test_register_creates_user_with_verification_email(
    user_repo, email_verif_repo, email_sender
):
    uc = RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://localhost:5173",
        skip_verification=False,
    )
    result = uc.execute("Foo@Example.com", "secret123", _password_hasher)
    assert result.requires_verification is True
    assert result.email == "foo@example.com"
    assert len(email_sender.sent) == 1
    assert email_sender.sent[0].to == "foo@example.com"
    assert "Verificá" in email_sender.sent[0].subject
    assert "/verify-email?token=" in email_sender.sent[0].text


def test_register_skip_verification_does_not_send_email(
    user_repo, email_verif_repo, email_sender
):
    uc = RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://localhost:5173",
        skip_verification=True,
    )
    result = uc.execute("foo@example.com", "secret123", _password_hasher)
    assert result.requires_verification is False
    assert len(email_sender.sent) == 0
    user = user_repo.get_by_email("foo@example.com")
    assert user is not None
    assert user.email_verified is True


def test_register_rejects_duplicate_email(
    user_repo, email_verif_repo, email_sender
):
    uc = RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://localhost:5173",
        skip_verification=False,
    )
    uc.execute("foo@example.com", "secret123", _password_hasher)
    with pytest.raises(UserAlreadyExistsError):
        uc.execute("FOO@example.com", "secret456", _password_hasher)


def test_login_issues_both_tokens(user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo):
    _register_verified(user_repo, email_verif_repo, email_sender)

    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    session = login.execute("foo@example.com", "secret123")

    assert session.email == "foo@example.com"
    assert session.access_token.startswith("jwt::")
    assert len(session.refresh_token) >= 40
    assert len(refresh_repo._items) == 1


def test_login_fails_for_unverified_user(user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo):
    RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://x", skip_verification=False,
    ).execute("foo@example.com", "secret123", _password_hasher)

    with pytest.raises(EmailNotVerifiedError):
        _make_login(user_repo, refresh_repo, twofa_pending_repo).execute("foo@example.com", "secret123")


def test_login_fails_with_wrong_password(user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo):
    _register_verified(user_repo, email_verif_repo, email_sender)
    with pytest.raises(InvalidCredentialsError):
        _make_login(user_repo, refresh_repo, twofa_pending_repo).execute("foo@example.com", "wrong")


def test_login_fails_for_unknown_email(user_repo, refresh_repo, twofa_pending_repo):
    with pytest.raises(InvalidCredentialsError):
        _make_login(user_repo, refresh_repo, twofa_pending_repo).execute("ghost@example.com", "anything")


def test_verify_email_issues_session_and_is_one_shot(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo
):
    RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://localhost:5173", skip_verification=False,
    ).execute("foo@example.com", "secret123", _password_hasher)

    raw = email_sender.sent[0].text.split("token=")[1].split()[0].strip()

    verify = VerifyEmail(
        user_repo, email_verif_repo, refresh_repo, twofa_pending_repo,
        token_creator=_token_creator,
    )
    session = verify.execute(raw)
    assert session.email == "foo@example.com"
    assert session.access_token.startswith("jwt::")

    user = user_repo.get_by_email("foo@example.com")
    assert user.email_verified is True
    assert user.email_verified_at is not None

    with pytest.raises(InvalidTokenError):
        verify.execute(raw)


def test_verify_email_rejects_invalid_token(
    user_repo, email_verif_repo, refresh_repo, twofa_pending_repo
):
    verify = VerifyEmail(
        user_repo, email_verif_repo, refresh_repo, twofa_pending_repo,
        token_creator=_token_creator,
    )
    with pytest.raises(InvalidTokenError):
        verify.execute("esto-no-es-un-token-valido")


def test_verify_email_rejects_expired_token(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo
):
    RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://x", skip_verification=False,
    ).execute("foo@example.com", "secret123", _password_hasher)
    raw = email_sender.sent[0].text.split("token=")[1].split()[0].strip()

    for t in list(email_verif_repo._items.values()):
        t.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    verify = VerifyEmail(
        user_repo, email_verif_repo, refresh_repo, twofa_pending_repo,
        token_creator=_token_creator,
    )
    with pytest.raises(TokenExpiredError):
        verify.execute(raw)


def test_resend_verification_replaces_old_token(
    user_repo, email_verif_repo, email_sender
):
    RegisterUser(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://localhost:5173", skip_verification=False,
    ).execute("foo@example.com", "secret123", _password_hasher)
    assert len(email_verif_repo._items) == 1

    resend = ResendVerification(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://localhost:5173",
    )
    resend.execute("foo@example.com")
    assert len(email_verif_repo._items) == 1
    assert len(email_sender.sent) == 2


def test_resend_verification_silent_for_unknown_email(
    user_repo, email_verif_repo, email_sender
):
    resend = ResendVerification(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://x",
    )
    resend.execute("ghost@example.com")
    assert len(email_sender.sent) == 0


def test_resend_verification_silent_for_already_verified(
    user_repo, email_verif_repo, email_sender
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    assert len(email_sender.sent) == 0

    resend = ResendVerification(
        user_repo, email_verif_repo, email_sender,
        frontend_url="http://x",
    )
    resend.execute("foo@example.com")
    assert len(email_sender.sent) == 0


def test_forgot_password_sends_email(
    user_repo, email_verif_repo, email_sender, pwd_reset_repo, refresh_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)

    forgot = ForgotPassword(
        user_repo, pwd_reset_repo, refresh_repo, email_sender,
        frontend_url="http://localhost:5173",
    )
    forgot.execute("foo@example.com")
    assert len(email_sender.sent) == 1
    assert "/reset-password?token=" in email_sender.sent[0].text


def test_forgot_password_silent_for_unknown_email(
    user_repo, pwd_reset_repo, refresh_repo, email_sender
):
    forgot = ForgotPassword(
        user_repo, pwd_reset_repo, refresh_repo, email_sender,
        frontend_url="http://x",
    )
    forgot.execute("ghost@example.com")
    assert len(email_sender.sent) == 0


def test_reset_password_changes_password_and_revokes_all_refreshs(
    user_repo, email_verif_repo, email_sender, pwd_reset_repo, refresh_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)

    # Login (crea un refresh)
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    session = login.execute("foo@example.com", "secret123")
    assert len(refresh_repo._items) == 1

    # Forgot password flow
    forgot = ForgotPassword(
        user_repo, pwd_reset_repo, refresh_repo, email_sender,
        frontend_url="http://localhost:5173",
    )
    forgot.execute("foo@example.com")
    raw = email_sender.sent[0].text.split("token=")[1].split()[0].strip()

    # Reset
    reset = ResetPassword(
        user_repo, pwd_reset_repo, refresh_repo,
        password_hasher=_password_hasher,
    )
    reset.execute(raw, "newpass456")

    # Login con la nueva password funciona
    _make_login(user_repo, refresh_repo, twofa_pending_repo).execute("foo@example.com", "newpass456")

    # Login con la vieja falla
    with pytest.raises(InvalidCredentialsError):
        _make_login(user_repo, refresh_repo, twofa_pending_repo).execute("foo@example.com", "secret123")

    # El refresh del viejo login está revocado
    all_tokens = list(refresh_repo._items.values())
    revoked = [t for t in all_tokens if t.revoked_at is not None]
    assert len(revoked) >= 1

    # El refresh original (de la sesión antes del reset) está específicamente revocado.
    old_refresh = refresh_repo.get_by_hash(
        __import__("hashlib").sha256(session.refresh_token.encode()).hexdigest()
    )
    assert old_refresh is not None
    assert old_refresh.is_revoked()


def test_reset_password_rejects_invalid_token(
    user_repo, pwd_reset_repo, refresh_repo
):
    reset = ResetPassword(
        user_repo, pwd_reset_repo, refresh_repo,
        password_hasher=_password_hasher,
    )
    with pytest.raises(InvalidTokenError):
        reset.execute("token-basura", "newpass456")


def test_reset_password_rejects_short_password(
    user_repo, pwd_reset_repo, refresh_repo
):
    reset = ResetPassword(
        user_repo, pwd_reset_repo, refresh_repo,
        password_hasher=_password_hasher,
    )
    with pytest.raises(ValidationError):
        reset.execute("cualquier-token-valido", "123")


# ── Refresh tokens (Phase 2) ─────────────────────────────────────────────


def test_refresh_rotates_token_in_same_family(
    user_repo, email_verif_repo, email_sender, refresh_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    s1 = login.execute("foo@example.com", "secret123")

    refresh = RefreshSession(
        user_repo, refresh_repo, token_creator=_token_creator
    )
    s2 = refresh.execute(s1.refresh_token)

    # Nuevo par emitido
    assert s2.access_token != s1.access_token
    assert s2.refresh_token != s1.refresh_token
    # Mismo user
    assert s2.user_id == s1.user_id

    # El viejo está revocado, el nuevo está activo
    assert len(refresh_repo._items) == 2
    revoked = [t for t in refresh_repo._items.values() if t.revoked_at is not None]
    assert len(revoked) == 1

    # Misma family
    families = {t.family_id for t in refresh_repo._items.values()}
    assert len(families) == 1


def test_refresh_rejects_revoked_token_and_invalidates_family(
    user_repo, email_verif_repo, email_sender, refresh_repo
):
    """Si alguien reusa un refresh ya revocado, TODA la family se invalida."""
    _register_verified(user_repo, email_verif_repo, email_sender)
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    s1 = login.execute("foo@example.com", "secret123")

    refresh = RefreshSession(
        user_repo, refresh_repo, token_creator=_token_creator
    )
    # Rotación legítima
    s2 = refresh.execute(s1.refresh_token)

    # Ahora alguien intenta reusar el viejo (ataque de robo)
    with pytest.raises(RefreshTokenReuseDetectedError):
        refresh.execute(s1.refresh_token)

    # La family entera está revocada — el s2 también
    assert all(t.revoked_at is not None for t in refresh_repo._items.values())


def test_refresh_rejects_unknown_token(user_repo, refresh_repo):
    refresh = RefreshSession(
        user_repo, refresh_repo, token_creator=_token_creator
    )
    with pytest.raises(InvalidTokenError):
        refresh.execute("token-que-no-existe")


def test_refresh_rejects_expired_token(
    user_repo, email_verif_repo, email_sender, refresh_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    s1 = login.execute("foo@example.com", "secret123")

    # Expirar manualmente
    for t in refresh_repo._items.values():
        t.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    refresh = RefreshSession(
        user_repo, refresh_repo, token_creator=_token_creator
    )
    with pytest.raises(TokenExpiredError):
        refresh.execute(s1.refresh_token)


def test_logout_revokes_refresh_token(
    user_repo, email_verif_repo, email_sender, refresh_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    s1 = login.execute("foo@example.com", "secret123")

    logout = Logout(refresh_repo)
    logout.execute(s1.refresh_token)

    # El refresh está revocado
    assert all(t.revoked_at is not None for t in refresh_repo._items.values())

    # Intentar refresh con el viejo falla con RefreshTokenReuseDetectedError
    refresh = RefreshSession(
        user_repo, refresh_repo, token_creator=_token_creator
    )
    with pytest.raises(RefreshTokenReuseDetectedError):
        refresh.execute(s1.refresh_token)


def test_logout_is_idempotent(user_repo, refresh_repo):
    """Logout con token inexistente o ya revocado no falla."""
    logout = Logout(refresh_repo)
    logout.execute("nope")  # no raise
    logout.execute("")  # no raise


# ── 2FA TOTP (Phase 3) ────────────────────────────────────────────────────


def _enable_totp_for(user, plain_secret: str | None = None):
    """Helper: encrypta un secret TOTP conocido y marca 2FA habilitado en el user."""
    if plain_secret is None:
        plain_secret = totp_svc.generate_totp_secret()
    user.totp_enabled = True
    user.totp_secret_encrypted = totp_svc.encrypt_secret(plain_secret)
    user.totp_enabled_at = datetime.now(timezone.utc)
    return plain_secret


def test_login_returns_pending_when_2fa_enabled(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    _enable_totp_for(user)

    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    outcome = login.execute("foo@example.com", "secret123")

    # Es LoginPending, no AuthSession
    from src.application.use_cases import AuthSession, LoginPending
    assert isinstance(outcome, LoginPending)
    assert not isinstance(outcome, AuthSession)
    assert outcome.email == "foo@example.com"
    assert len(outcome.pending_token) >= 40

    # Se creó un pending en la DB
    assert len(twofa_pending_repo._items) == 1


def test_login_returns_session_when_2fa_not_enabled(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    outcome = login.execute("foo@example.com", "secret123")

    from src.application.use_cases import AuthSession
    assert isinstance(outcome, AuthSession)


def test_setup_totp_start_generates_secret(
    user_repo, email_verif_repo, email_sender
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")

    result = SetupTotpStart(user_repo).execute(user.id)

    # Devuelve QR + manual key
    assert result.qr_data_url.startswith("data:image/png;base64,")
    assert len(result.manual_key) == 32  # base32 32 chars (160 bits)
    assert result.otpauth_uri.startswith("otpauth://totp/")

    # El user tiene el secret encriptado pero totp_enabled sigue en False
    user_after = user_repo.get_by_id(user.id)
    assert user_after.totp_enabled is False
    assert user_after.totp_secret_encrypted is not None


def test_setup_totp_start_rejects_already_enabled(
    user_repo, email_verif_repo, email_sender
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    _enable_totp_for(user)

    with pytest.raises(TwoFactorAlreadyEnabledError):
        SetupTotpStart(user_repo).execute(user.id)


def test_setup_totp_confirm_enables_and_returns_backup_codes(
    user_repo, email_verif_repo, email_sender, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")

    # Iniciar setup
    SetupTotpStart(user_repo).execute(user.id)
    user = user_repo.get_by_email("foo@example.com")
    secret = totp_svc.decrypt_secret(user.totp_secret_encrypted)

    # Confirmar con el code actual
    code = totp_svc.current_totp(secret)
    result = SetupTotpConfirm(user_repo, backup_repo).execute(user.id, code)

    # Devuelve 10 backup codes
    assert len(result.backup_codes) == 10
    for c in result.backup_codes:
        assert len(c) == 9  # "XXXX-1234"
        assert c[4] == "-"

    # 2FA habilitado
    user_after = user_repo.get_by_id(user.id)
    assert user_after.totp_enabled is True
    assert user_after.totp_enabled_at is not None

    # Backup codes guardados
    assert len(backup_repo.list_for_user(user.id)) == 10


def test_setup_totp_confirm_rejects_wrong_code(
    user_repo, email_verif_repo, email_sender, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")

    SetupTotpStart(user_repo).execute(user.id)

    with pytest.raises(InvalidTwoFactorCodeError):
        SetupTotpConfirm(user_repo, backup_repo).execute(user.id, "000000")


def test_verify_two_factor_with_totp_code(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    
    plain = _enable_totp_for(user)

    # Login → pending
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    pending = login.execute("foo@example.com", "secret123")

    # Verify con TOTP actual
    verify = VerifyTwoFactor(
        user_repo, twofa_pending_repo, backup_repo, refresh_repo,
        token_creator=_token_creator,
    )
    code = totp_svc.current_totp(plain)
    session = verify.execute(pending.pending_token, code)

    assert session.user_id == user.id
    assert session.access_token.startswith("jwt::")
    assert len(twofa_pending_repo._items) == 0  # consumed


def test_verify_two_factor_with_backup_code(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    _enable_totp_for(user)

    # Generar backup codes manualmente
    pairs = totp_svc.generate_backup_codes(n=10)
    from src.domain.entities import BackupCode as BC
    entities = [
        BC(id=str(uuid.uuid4()), user_id=user.id, code_hash=p.hash, created_at=datetime.now(timezone.utc))
        for p in pairs
    ]
    backup_repo.create_many(entities)

    # Login → pending
    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    pending = login.execute("foo@example.com", "secret123")

    # Verify con backup code (primer código)
    verify = VerifyTwoFactor(
        user_repo, twofa_pending_repo, backup_repo, refresh_repo,
        token_creator=_token_creator,
    )
    session = verify.execute(pending.pending_token, pairs[0].raw)

    assert session.user_id == user.id

    # El backup code está usado
    used = [c for c in backup_repo.list_for_user(user.id) if c.is_used()]
    assert len(used) == 1

    # Reusarlo falla
    with pytest.raises(InvalidTwoFactorCodeError):
        verify.execute(pending.pending_token, pairs[0].raw)


def test_verify_two_factor_rejects_invalid_code(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    _enable_totp_for(user)

    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    pending = login.execute("foo@example.com", "secret123")

    verify = VerifyTwoFactor(
        user_repo, twofa_pending_repo, backup_repo, refresh_repo,
        token_creator=_token_creator,
    )
    with pytest.raises(InvalidTwoFactorCodeError):
        verify.execute(pending.pending_token, "999999")


def test_verify_two_factor_rejects_expired_pending(
    user_repo, email_verif_repo, email_sender, refresh_repo, twofa_pending_repo, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    
    plain = _enable_totp_for(user)

    login = _make_login(user_repo, refresh_repo, twofa_pending_repo)
    pending = login.execute("foo@example.com", "secret123")

    # Expirar manualmente
    for p in twofa_pending_repo._items.values():
        p.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    verify = VerifyTwoFactor(
        user_repo, twofa_pending_repo, backup_repo, refresh_repo,
        token_creator=_token_creator,
    )
    code = totp_svc.current_totp(plain)
    with pytest.raises(InvalidTwoFactorCodeError):
        verify.execute(pending.pending_token, code)


def test_disable_totp_requires_password_and_code(
    user_repo, email_verif_repo, email_sender, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    
    plain = _enable_totp_for(user)

    disable = DisableTotp(user_repo, backup_repo, password_verifier=_password_verifier)

    # Password incorrecto
    with pytest.raises(InvalidCredentialsError):
        disable.execute(user.id, "wrong-password", "000000")

    # Password correcto + TOTP code correcto
    code = totp_svc.current_totp(plain)
    disable.execute(user.id, "secret123", code)

    # 2FA deshabilitado
    user_after = user_repo.get_by_id(user.id)
    assert user_after.totp_enabled is False
    assert user_after.totp_secret_encrypted is None


def test_disable_totp_rejects_when_not_enabled(
    user_repo, email_verif_repo, email_sender, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")

    disable = DisableTotp(user_repo, backup_repo, password_verifier=_password_verifier)
    with pytest.raises(TwoFactorNotEnabledError):
        disable.execute(user.id, "secret123", "000000")


def test_regenerate_backup_codes_replaces_old(
    user_repo, email_verif_repo, email_sender, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")

    # Setup completo (start + confirm con code actual)
    SetupTotpStart(user_repo).execute(user.id)
    secret = totp_svc.decrypt_secret(user_repo.get_by_id(user.id).totp_secret_encrypted)
    SetupTotpConfirm(user_repo, backup_repo).execute(user.id, totp_svc.current_totp(secret))
    initial = backup_repo.list_for_user(user.id)
    assert len(initial) == 10

    # Regenerar
    regen = RegenerateBackupCodes(
        user_repo, backup_repo, password_verifier=_password_verifier
    )
    new_codes = regen.execute(user.id, "secret123")
    assert len(new_codes) == 10
    after = backup_repo.list_for_user(user.id)
    assert len(after) == 10
    new_hashes = {c.code_hash for c in after}
    initial_hashes = {c.code_hash for c in initial}
    assert new_hashes.isdisjoint(initial_hashes)


def test_regenerate_backup_codes_requires_password(
    user_repo, email_verif_repo, email_sender, backup_repo
):
    _register_verified(user_repo, email_verif_repo, email_sender)
    user = user_repo.get_by_email("foo@example.com")
    _enable_totp_for(user)

    regen = RegenerateBackupCodes(
        user_repo, backup_repo, password_verifier=_password_verifier
    )
    with pytest.raises(InvalidCredentialsError):
        regen.execute(user.id, "wrong-password")



