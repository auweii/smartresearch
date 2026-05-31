import fitz  # PyMuPDF

def pdf_to_text(path: str) -> str:
    """
    Extract selectable text directly from a PDF using PyMuPDF.
    If pages fail (encrypted / malformed), skip them gracefully.
    """
    doc = fitz.open(path)
    chunks = []
    for page in doc:
        try:
            chunks.append(page.get_text() or "")
        except Exception:
            continue
    doc.close()
    return "\n".join(chunks).strip()