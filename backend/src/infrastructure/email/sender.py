"""Email sender: abstracción para enviar emails.

Dos implementaciones:
- ``ConsoleEmailSender`` (dev/test): loguea a stdout via el logger de Python.
- ``SmtpEmailSender`` (prod): SMTP genérico con TLS opcional.

Se elige automáticamente en ``get_email_sender()``: si ``SMTP_HOST`` está
seteado, va SMTP; si no, console.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol

log = logging.getLogger(__name__)


class EmailSender(Protocol):
    """Contrato mínimo para enviar un email."""

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        ...


class ConsoleEmailSender:
    """Imprime emails en stdout. Útil en dev/test — no requiere SMTP."""

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        # Separador para que sea fácil de grep en los logs
        log.info("=" * 60)
        log.info("EMAIL → to=%s", to)
        log.info("SUBJECT: %s", subject)
        log.info("-" * 60)
        log.info("\n%s", text)
        log.info("=" * 60)


class SmtpEmailSender:
    """SMTP genérico. Funciona con Gmail, SendGrid, Mailgun, Resend, etc.

    Variables de entorno necesarias:
        SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
        SMTP_FROM_EMAIL, SMTP_FROM_NAME (opcional)
        SMTP_TLS ("true" para STARTTLS en el puerto 587; implícito TLS en 465).
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str = "",
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
        msg["To"] = to
        msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        if self.port == 465 and self.use_tls:
            # Implicit TLS (SMTPS)
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.host, self.port, context=ctx, timeout=15) as s:
                s.login(self.username, self.password)
                s.send_message(msg)
        else:
            # STARTTLS o plano
            with smtplib.SMTP(self.host, self.port, timeout=15) as s:
                s.ehlo()
                if self.use_tls:
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                s.login(self.username, self.password)
                s.send_message(msg)


def get_email_sender() -> EmailSender:
    """Devuelve el sender según la config del entorno.

    - Si ``SMTP_HOST`` está seteado → ``SmtpEmailSender``.
    - Si no → ``ConsoleEmailSender`` (dev).
    """
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        log.info("Email sender: Console (SMTP_HOST no configurado)")
        return ConsoleEmailSender()

    port = int(os.environ.get("SMTP_PORT", "587"))
    sender = SmtpEmailSender(
        host=host,
        port=port,
        username=os.environ.get("SMTP_USERNAME", ""),
        password=os.environ.get("SMTP_PASSWORD", ""),
        from_email=os.environ.get("SMTP_FROM_EMAIL", "noreply@localhost"),
        from_name=os.environ.get("SMTP_FROM_NAME", "Creator CV"),
        use_tls=os.environ.get("SMTP_TLS", "true").lower() != "false",
    )
    log.info("Email sender: SMTP → %s:%s", host, port)
    return sender
