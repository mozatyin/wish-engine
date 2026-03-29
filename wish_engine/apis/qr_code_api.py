"""QR code generation. Free, no key."""
from __future__ import annotations

def get_qr_url(text: str, size: int = 200) -> str:
    """Returns URL to a QR code image for the given text."""
    from urllib.parse import quote
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={quote(text)}"

def is_available() -> bool: return True
