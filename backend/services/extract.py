from PyPDF2 import PdfReader

def pdf_to_text(path: str) -> str:
    """
    Extract selectable text directly from a PDF.
    If pages fail (encrypted / malformed), skip them gracefully.
    """
    reader = PdfReader(path)
    chunks = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(chunks).strip()
