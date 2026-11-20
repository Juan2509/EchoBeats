"""Bounded PDF extraction and per-page OCR on scanned pages."""

import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unicodedata

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 12
MAX_CHUNKS = 40
SIGNATURES = Path("/var/lib/clamav")
HEADING = re.compile(r"^\s*(?:(?:cap[ií]tulo|secci[oó]n|ap[eé]ndice|chapter|section|appendix)\s+[\wIVX]+|\d+(?:\.\d+)+\s+)\S*.*$", re.IGNORECASE)


class DocumentError(Exception):
    pass


def scanner_ready():
    return any(path.is_file() for pattern in ("*.cvd", "*.cld") for path in SIGNATURES.glob(pattern))


def run(command, *, timeout=12):
    try:
        return subprocess.run(
            ["prlimit", "--as=1610612736", "--fsize=4194304", "--cpu=35", "--", *command],
            capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout,
            env={"PATH": os.defpath, "LC_ALL": "C", "OMP_THREAD_LIMIT": "1"},
        )
    except (OSError, subprocess.TimeoutExpired):
        raise DocumentError("processing_limit") from None


def checked(command):
    result = run(command)
    if result.returncode:
        raise DocumentError("invalid_pdf")
    return result.stdout.decode("utf-8", errors="replace")


def scan(path):
    result = run(["clamscan", "--database", str(SIGNATURES), "--no-summary", "--alert-exceeds-max=yes", str(path)], timeout=40)
    if result.returncode == 1:
        raise DocumentError("unsafe_pdf")
    if result.returncode:
        raise DocumentError("scanner_unavailable")


def split_page(text):
    text = unicodedata.normalize("NFC", text)
    text = " ".join("".join(c if c.isprintable() or c.isspace() else " " for c in text).split())
    cursor = 0
    while cursor < len(text):
        end = min(len(text), cursor + 1600)
        if end < len(text):
            boundary = text.rfind(" ", cursor + 1200, end)
            if boundary != -1:
                end = boundary
        yield text[cursor:end].strip()
        cursor = end - 120 if end < len(text) else end


def page_sections(text, inherited):
    section, lines = inherited, []
    for line in text.splitlines():
        heading = "".join(c if c.isprintable() else " " for c in line).strip()
        if len(heading) <= 200 and HEADING.match(heading):
            if lines:
                yield section, "\n".join(lines)
            section, lines = heading, []
        lines.append(line)
    if lines:
        yield section, "\n".join(lines)


def extract(pdf, stop):
    chunks = []
    section = None
    with TemporaryDirectory(prefix="echobeats-pdf-") as directory:
        root = Path(directory)
        path = root / "upload.pdf"
        path.write_bytes(pdf)
        scan(path)
        info = checked(["pdfinfo", str(path)])
        pages = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
        if not pages or re.search(r"^Encrypted:\s+yes", info, re.MULTILINE):
            raise DocumentError("invalid_pdf")
        count = int(pages[1])
        if not 1 <= count <= MAX_PAGES:
            raise DocumentError("page_limit")
        for page in range(1, count + 1):
            if stop.is_set():
                raise InterruptedError
            number = str(page)
            output = root / "page.txt"
            checked(["pdftotext", "-layout", "-enc", "UTF-8", "-f", number, "-l", number, str(path), str(output)])
            text = output.read_text("utf-8", errors="replace")
            extraction = "text"
            if not any(c.isalnum() for c in text):
                image = root / "scan"
                checked(["pdftoppm", "-f", number, "-l", number, "-singlefile", "-scale-to", "1800", "-png", str(path), str(image)])
                checked(["tesseract", str(image.with_suffix(".png")), str(root / "ocr"), "-l", "spa+eng"])
                text = (root / "ocr.txt").read_text("utf-8", errors="replace")
                extraction = "ocr"
            ordinal = 0
            for section, section_text in page_sections(text, section):
                for piece in split_page(section_text):
                    ordinal += 1
                    chunks.append({
                        "page": page, "ordinal": ordinal, "section": section,
                        "extraction": extraction, "content": piece,
                    })
                    if len(chunks) > MAX_CHUNKS:
                        raise DocumentError("chunk_limit")
    if not chunks:
        raise DocumentError("no_text")
    return chunks
