"""Optional PDF export through LibreOffice (headless)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

_WINDOWS_PATHS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]
_MAC_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def find_soffice() -> Optional[str]:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in [*_WINDOWS_PATHS, _MAC_PATH]:
        if os.path.isfile(candidate):
            return candidate
    return None


class PdfError(Exception):
    pass


def convert(docx: Path, soffice: str, timeout: int = 600) -> Path:
    """Convert ``docx`` to a PDF next to it and return the PDF path."""
    out_dir = docx.parent
    # A private profile avoids clashing with a LibreOffice window already open.
    with tempfile.TemporaryDirectory(prefix="codeappendix-lo-") as profile:
        cmd = [
            soffice,
            f"-env:UserInstallation={Path(profile).as_uri()}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(docx),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise PdfError(f"LibreOffice took longer than {timeout}s") from None
        except OSError as exc:
            raise PdfError(str(exc)) from None
    pdf = out_dir / (docx.stem + ".pdf")
    if proc.returncode != 0 or not pdf.is_file():
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        message = detail[-1] if detail else f"exit code {proc.returncode}"
        if "could not be loaded" in message:
            message += " (is LibreOffice Writer installed? e.g. apt install libreoffice-writer)"
        raise PdfError(message)
    return pdf


def count_pages(pdf: Path) -> Optional[int]:
    """Page count from the PDF page tree, or None if it cannot be read."""
    try:
        data = pdf.read_bytes()
    except OSError:
        return None
    counts = [int(m) for m in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data)]
    counts += [int(m) for m in re.findall(rb"/Count\s+(\d+)[^>]*?/Type\s*/Pages\b", data)]
    return max(counts) if counts else None
