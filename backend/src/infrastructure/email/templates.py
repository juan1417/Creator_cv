"""Plantillas de email (ES).

Funciones puras: dado (to, link, ...) devuelven (subject, html, text).
Sin lógica de envío — eso lo hace ``email/sender.py``.
"""
from __future__ import annotations


def verification_email(*, verify_url: str, frontend_url: str) -> tuple[str, str, str]:
    """Email de verificación de cuenta."""
    subject = "Verificá tu cuenta de Creator CV"
    text = (
        f"¡Bienvenido a Creator CV!\n\n"
        f"Para activar tu cuenta, hacé click en el siguiente enlace:\n\n"
        f"  {verify_url}\n\n"
        f"El enlace expira en 24 horas.\n\n"
        f"Si no creaste esta cuenta, podés ignorar este mensaje.\n\n"
        f"— Creator CV ({frontend_url})"
    )
    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #1a1a1a;">¡Bienvenido a Creator CV!</h2>
        <p>Para activar tu cuenta, hacé click en el botón:</p>
        <p style="text-align: center; margin: 32px 0;">
            <a href="{verify_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                Verificar mi email
            </a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">O copiá y pegá este enlace en tu navegador:</p>
        <p style="word-break: break-all; color: #6b7280; font-size: 13px;">{verify_url}</p>
        <p style="color: #9ca3af; font-size: 12px; margin-top: 32px;">El enlace expira en 24 horas. Si no creaste esta cuenta, podés ignorar este mensaje.</p>
    </div>
    """.strip()
    return subject, html, text


def password_reset_email(*, reset_url: str, frontend_url: str) -> tuple[str, str, str]:
    """Email de reseteo de contraseña."""
    subject = "Restablecé tu contraseña de Creator CV"
    text = (
        f"Recibimos una solicitud para restablecer la contraseña de tu cuenta.\n\n"
        f"Para crear una nueva contraseña, hacé click en el siguiente enlace:\n\n"
        f"  {reset_url}\n\n"
        f"El enlace expira en 1 hora. Si no solicitaste esto, podés ignorar este mensaje — tu contraseña no cambia.\n\n"
        f"— Creator CV ({frontend_url})"
    )
    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #1a1a1a;">Restablecer contraseña</h2>
        <p>Recibimos una solicitud para cambiar la contraseña de tu cuenta. Si fuiste vos, hacé click en el botón:</p>
        <p style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                Crear nueva contraseña
            </a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">O copiá y pegá este enlace en tu navegador:</p>
        <p style="word-break: break-all; color: #6b7280; font-size: 13px;">{reset_url}</p>
        <p style="color: #9ca3af; font-size: 12px; margin-top: 32px;">El enlace expira en 1 hora. Si no solicitaste esto, podés ignorar este mensaje.</p>
    </div>
    """.strip()
    return subject, html, text
