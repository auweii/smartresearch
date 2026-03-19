# services/pdf_processing.py

from services.extract import pdf_to_text
from services.summarize import textrankish_summary
from services.metadata import enrich_from_text

def process_pdf(file_path: str, max_summary_sentences: int = 5) -> dict:
    """
    Extract text, generate summary, and enrich metadata.
    Returns a dict suitable for storing in your database.
    """
    text = pdf_to_text(file_path)

    if not text.strip():
        text = "No readable content found in PDF."

    # Extractive summary
    summary = textrankish_summary(text, max_sentences=max_summary_sentences)

    # Metadata enrichment
    meta = enrich_from_text(text) or {}

    return {
        "full_text": text,
        "summary": summary,
        "abstract": summary,  # optional: reuse summary for abstract
        "meta": meta
    }
