from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract

def pdf_to_text(path: str) -> str:
    """
    Extract selectable text directly from a PDF.
    If a page has no selectable text, use OCR instead.
    If pages fail, skip them gracefully.
    """
    reader = PdfReader(path)
    chunks = []

    for i, page in enumerate(reader.pages):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""

        if not text:
            try:
                images = convert_from_path(path, first_page=i + 1, last_page=i + 1)
                text = pytesseract.image_to_string(images[0]).strip() if images else ""
            except Exception:
                text = ""

        if text:
            chunks.append(text)

    return "\n".join(chunks).strip()
