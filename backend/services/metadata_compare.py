from difflib import SequenceMatcher

def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def compare_metadata(pdf: dict, ext: dict) -> dict:
    title_sim = _sim(pdf.get("title"), ext.get("title"))
    authors_sim = _sim(
        " ".join(pdf.get("authors", [])),
        " ".join(ext.get("authors", [])),
    )

    year_pdf = pdf.get("year")
    year_ext = ext.get("year")
    year_match = (year_pdf == year_ext) if year_pdf and year_ext else True

    confidence = (
        0.6 * title_sim +
        0.3 * authors_sim +
        0.1 * (1.0 if year_match else 0.0)
    )

    return {
        "title_match": title_sim > 0.8,
        "authors_match": authors_sim > 0.7,
        "year_match": year_match,
        "confidence": round(confidence, 2),
        "reliable": confidence >= 0.75,
    }
