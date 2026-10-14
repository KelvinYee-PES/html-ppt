"""Optional high-fidelity slide preview via LibreOffice."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def find_libreoffice_binary() -> str | None:
    """Find soffice executable if installed."""
    # Check standard PATH
    which_soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if which_soffice:
        return which_soffice

    # Check common Windows paths
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def is_libreoffice_available() -> bool:
    return find_libreoffice_binary() is not None


def convert_pptx_to_pdf(pptx_bytes: bytes) -> bytes | None:
    """Convert PPTX to PDF using headless LibreOffice."""
    binary = find_libreoffice_binary()
    if not binary:
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_pptx = Path(tmpdir) / "input.pptx"
        tmp_pptx.write_bytes(pptx_bytes)

        cmd = [
            binary,
            "--headless",
            "--convert-to",
            "pdf",
            str(tmp_pptx),
            "--outdir",
            tmpdir,
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=30)
            if res.returncode == 0:
                pdf_path = Path(tmpdir) / "input.pdf"
                if pdf_path.exists():
                    return pdf_path.read_bytes()
        except Exception:
            return None
    return None
