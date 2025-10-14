from pdf2image import convert_from_path
import pytesseract

def ocr_pdf_to_text(path: str, dpi=300, lang="eng") -> str:
    """
    Convert a scanned PDF into machine-readable text via OCR.
    Uses pdf2image + pytesseract, one page at a time.
    """
    images = convert_from_path(path, dpi=dpi)
    texts = [pytesseract.image_to_string(img, lang=lang) for img in images]
    return "\n".join(texts).strip()
