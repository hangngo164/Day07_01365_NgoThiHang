"""OCR PDF scan trong data/pdf va cap nhat body cua Markdown rong trong data/md."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdf"
MD_DIR = ROOT / "data" / "md"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
PDFTOPPM = Path(
    r"C:\Users\PC\AppData\Local\Microsoft\WinGet\Packages"
    r"\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\poppler-25.07.0\Library\bin\pdftoppm.exe"
)
TESSDATA_DIR = ROOT / "tools" / "ocr" / "tessdata"


def front_matter_and_body(text: str) -> tuple[str, str]:
    match = re.match(r"\A(---\n.*?\n---\n*)(.*)\Z", text, re.DOTALL)
    if not match:
        return "", text
    return match.group(1), match.group(2)


def has_document_text(body: str) -> bool:
    """Mot heading don le khong duoc coi la noi dung da trich xuat."""
    return any(
        line.strip() and not line.lstrip().startswith("#")
        for line in body.splitlines()
    )


def source_pdf_name(front_matter: str) -> str | None:
    match = re.search(r"^source_file:\s*(.+)$", front_matter, re.MULTILINE)
    return match.group(1).strip() if match else None


def ocr_pdf(pdf_path: Path) -> list[str]:
    pages: list[str] = []
    with tempfile.TemporaryDirectory(prefix="lab7_ocr_") as temp_dir:
        temp_path = Path(temp_dir)
        subprocess.run(
            [str(PDFTOPPM), "-r", "200", "-png", str(pdf_path), str(temp_path / "page")],
            check=True,
        )
        for image_path in sorted(temp_path.glob("page-*.png")):
            result = subprocess.run(
                [
                    str(TESSERACT),
                    str(image_path),
                    "stdout",
                    "-l",
                    "vie",
                    "--tessdata-dir",
                    str(TESSDATA_DIR),
                    "--oem",
                    "1",
                    "--psm",
                    "6",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            pages.append(result.stdout.strip())
    return pages


def main() -> None:
    if not TESSERACT.exists() or not PDFTOPPM.exists():
        raise RuntimeError("Khong tim thay Tesseract hoac Poppler.")

    for md_path in sorted(MD_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        front_matter, body = front_matter_and_body(text)
        if not front_matter or has_document_text(body):
            continue

        source_name = source_pdf_name(front_matter)
        pdf_path = PDF_DIR / source_name if source_name else None
        if not pdf_path or not pdf_path.exists():
            print(f"SKIP {md_path.name}: khong tim thay PDF nguon")
            continue

        print(f"OCR {pdf_path.name}", flush=True)
        pages = ocr_pdf(pdf_path)
        title = re.search(r"^title:\s*(.+)$", front_matter, re.MULTILINE)
        heading = title.group(1).strip() if title else md_path.stem
        page_text = "\n\n".join(
            f"## Trang {number}\n\n{page}" for number, page in enumerate(pages, start=1) if page
        )
        new_body = f"# {heading}\n\n> Noi dung duoc OCR tu PDF scan. Can doi chieu PDF goc truoc khi dung lam tai lieu chinh thuc.\n\n{page_text}\n"
        md_path.write_text(front_matter + "\n" + new_body, encoding="utf-8")
        print(f"DONE {md_path.name}: {len(pages)} trang", flush=True)


if __name__ == "__main__":
    main()
