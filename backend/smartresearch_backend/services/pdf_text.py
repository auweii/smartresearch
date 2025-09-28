import fitz  # PyMuPDF

def extract_text(pdf_path: str, max_pages: int | None = 40) -> str:
    doc = fitz.open(pdf_path)
    n = len(doc) if max_pages is None else min(max_pages, len(doc))
    txt = "\n".join((doc[i].get_text("text") or "") for i in range(n))
    doc.close()
    return txt
