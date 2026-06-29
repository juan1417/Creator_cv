"""QR code generation para otpauth:// URIs."""
from __future__ import annotations

import io

import qrcode


def make_qr_png(data: str) -> bytes:
    """Genera un QR PNG (bytes) a partir de un string (otpauth:// URI)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_qr_data_url(data: str) -> str:
    """Genera un data URL ``data:image/png;base64,...`` listo para `<img src>``."""
    import base64

    png = make_qr_png(data)
    b64 = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{b64}"
