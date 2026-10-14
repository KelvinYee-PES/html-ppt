"""Small HTTP helpers shared by API routes."""
from __future__ import annotations

from urllib.parse import quote


def content_disposition(filename: str) -> str:
    """Build an attachment header that survives non-Latin-1 filenames (RFC 6266 / 5987).

    Starlette encodes headers as Latin-1, so a raw title like "Strategie für 2027 – €"
    would raise. We send an ASCII fallback plus the UTF-8 ``filename*`` form.
    """
    ascii_name = filename.encode("ascii", "ignore").decode().replace('"', "").replace("\\", "")
    ascii_name = ascii_name.strip() or "download"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
