import fitz
import pytesseract
from PIL import Image
import io


def ocr_pdf_to_text(path: str, dpi=200, lang="eng") -> str:
    # renders each page as an image then runs tesseract OCR on it
    doc = fitz.open(path)
    texts = []

    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        texts.append(pytesseract.image_to_string(img, lang=lang))

    doc.close()
    return "\n".join(texts).strip()