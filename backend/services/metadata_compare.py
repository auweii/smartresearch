from difflib import SequenceMatcher
import requests


def _is_plausible(crossref_title: str, local_title: str) -> bool:
    if not crossref_title or not local_title:
        return False
    sim = SequenceMatcher(None, crossref_title.lower(), local_title.lower()).ratio()
    return sim > 0.7


def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _query_crossref(doi: str = None, title: str = None) -> dict:
    # try DOI lookup first, fall back to title search
    try:
        if doi:
            r = requests.get(
                f"https://api.crossref.org/works/{doi}",
                timeout=3,
            )
            if r.status_code == 200:
                it = r.json().get("message", {})
                crossref_title = (it.get("title") or [None])[0]
                if not _is_plausible(crossref_title, title or ""):
                    return {}
                return {
                    "title": crossref_title,
                    "authors": [
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in it.get("author", [])
                    ],
                    "year": it.get("issued", {}).get("date-parts", [[None]])[0][0],
                    "venue": (it.get("container-title") or [None])[0],
                    "doi": it.get("DOI"),
                }

        if title:
            r = requests.get(
                "https://api.crossref.org/works",
                params={"query.title": title, "rows": 1},
                timeout=3,
            )
            if r.status_code == 200:
                items = r.json().get("message", {}).get("items", [])
                if items:
                    it = items[0]
                    crossref_title = (it.get("title") or [None])[0]
                    if not _is_plausible(crossref_title, title or ""):
                        return {}
                    return {
                        "title": crossref_title,
                        "authors": [
                            f"{a.get('given', '')} {a.get('family', '')}".strip()
                            for a in it.get("author", [])
                        ],
                        "year": it.get("issued", {}).get("date-parts", [[None]])[0][0],
                        "venue": (it.get("container-title") or [None])[0],
                        "doi": it.get("DOI"),
                    }
    except Exception:
        pass

    return {}


def compare_metadata(pdf: dict, title: str = None, doi: str = None) -> dict:
    # compare locally extracted metadata against CrossRef and return confidence score
    ext = _query_crossref(doi=doi, title=title or pdf.get("title"))

    if not ext:
        return {
            "title_match": False,
            "authors_match": False,
            "year_match": True,
            "confidence": 1.0,
            "reliable": False,
            "external": {},
        }

    title_sim = _sim(pdf.get("title"), ext.get("title"))
    authors_sim = _sim(
        " ".join(pdf.get("authors") or []),
        " ".join(ext.get("authors") or []),
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
        "external": ext,
    }