"""TOTP (RFC 6238) + Fernet encryption at rest.

El secret del usuario se guarda encriptado con Fernet (AES-128-CBC + HMAC-SHA256).
La key de Fernet viene de ``ENCRYPTION_KEY`` y debe estar en el entorno.
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import string
from dataclasses import dataclass

import pyotp
from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Falta ENCRYPTION_KEY en el entorno. "
            "Generar con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode())
    except Exception as e:
        raise RuntimeError(f"ENCRYPTION_KEY inválida: {e}") from e


# ── Encryption at rest ───────────────────────────────────────────────────


def encrypt_secret(plain: str) -> bytes:
    return _get_fernet().encrypt(plain.encode("utf-8"))


def decrypt_secret(enc: bytes) -> str:
    try:
        return _get_fernet().decrypt(enc).decode("utf-8")
    except InvalidToken as e:
        raise RuntimeError(
            "No se pudo desencriptar el TOTP secret. ¿Rotaste ENCRYPTION_KEY?"
        ) from e


# ── TOTP ────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Genera un secret base32 de 32 chars (160 bits de entropía)."""
    return pyotp.random_base32(length=32)


def verify_totp(secret: str, code: str, valid_window: int = 1) -> bool:
    """Verifica un código TOTP de 6 dígitos. ``valid_window=1`` da tolerancia
    de ±30 segundos (un step TOTP)."""
    if not code or not code.strip():
        return False
    code = code.strip().replace(" ", "")
    if not code.isdigit() or len(code) != 6:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)


def provisioning_uri(secret: str, email: str, issuer: str | None = None) -> str:
    """Genera el otpauth:// URI que el cliente escanea con su app."""
    issuer_final = issuer or os.environ.get("TOTP_ISSUER", "Creator CV")
    return pyotp.TOTP(secret).provisioning_uri(
        name=email, issuer_name=issuer_final
    )


def current_totp(secret: str) -> str:
    """Devuelve el código TOTP actual (sólo para tests / debug)."""
    return pyotp.TOTP(secret).now()


# ── Backup codes ─────────────────────────────────────────────────────────


@dataclass
class BackupCodePair:
    """Un código generado: ``raw`` (se muestra al usuario UNA vez) y ``hash``
    (lo que va a la DB)."""

    raw: str
    hash: str


def _normalize_backup_code(raw: str) -> str:
    """Normaliza: uppercase + sin guiones ni espacios."""
    return raw.strip().upper().replace("-", "").replace(" ", "")


def _format_backup_code(normalized: str) -> str:
    """Formato legible: ``ABCD-1234`` (4 chars + 4 chars)."""
    if len(normalized) != 8:
        return normalized
    return f"{normalized[:4]}-{normalized[4:]}"


def generate_backup_codes(n: int = 10) -> list[BackupCodePair]:
    """Genera ``n`` códigos con su hash. Los códigos son 8 chars (letras + dígitos)."""
    alphabet = string.ascii_uppercase + string.digits
    pairs: list[BackupCodePair] = []
    seen: set[str] = set()
    while len(pairs) < n:
        raw_normalized = "".join(secrets.choice(alphabet) for _ in range(8))
        if raw_normalized in seen:
            continue
        seen.add(raw_normalized)
        pairs.append(
            BackupCodePair(
                raw=_format_backup_code(raw_normalized),
                hash=hashlib.sha256(raw_normalized.encode("utf-8")).hexdigest(),
            )
        )
    return pairs


def hash_backup_code(raw: str) -> str:
    """Hash del código normalizado, para comparar contra la DB."""
    return hashlib.sha256(_normalize_backup_code(raw).encode("utf-8")).hexdigest()


def looks_like_backup_code(raw: str) -> bool:
    """Heurística: si tiene guión o letras (TOTP codes son sólo dígitos)."""
    return "-" in raw or any(c.isalpha() for c in raw)


def normalize_for_lookup(raw: str) -> str:
    return _normalize_backup_code(raw)
