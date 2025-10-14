import re
import requests

def enrich_from_text(text: str):
    """
    Try to extract bibliographic metadata from the first few lines of a document
    using the CrossRef API. Adds sanity checks to avoid misclassifying 
    random content (like gym guides or cookbooks) as academic work.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return None

    # quick reject for clearly non-academic stuff
    lower_text = text.lower()
    banned_terms = ["recipe", "calorie", "workout", "gym", "cookbook", "nutrition", "meal prep"]
    if any(k in lower_text for k in banned_terms):
        return None

    for line in lines[:10]:
        # skip obvious junk (copyright, ISBNs, etc.)
        if re.search(r"(copyright|all rights reserved|reproduction|isbn|contents)", line, re.I):
            continue
        if len(line.split()) < 4:
            continue

        try:
            # ask CrossRef who the hell wrote this thing
            r = requests.get(
                "https://api.crossref.org/works",
                params={"query.bibliographic": line, "rows": 1},
                timeout=10,
            )
            data = r.json().get("message", {}).get("items", [])
            if not data:
                continue

            it = data[0]
            meta = {
                "title": (it.get("title") or [None])[0],
                "authors": [
                    f"{a.get('given','')} {a.get('family','')}".strip()
                    for a in it.get("author", [])
                ],
                "year": it.get("issued", {}).get("date-parts", [[None]])[0][0],
                "doi": it.get("DOI"),
                "venue": (it.get("container-title") or [None])[0],
                "publisher": it.get("publisher"),
            }

            # sanity filters — because not everything CrossRef returns is sane
            if not meta["title"]:
                return None
            if meta["title"].strip().lower() in {
                "copyright", "untitled", "contents", "index", "table of contents"
            }:
                return None

            # basic DOI format validation
            doi = meta.get("doi")
            if doi and not re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", doi):
                meta["doi"] = None

            # skip false positives
            if meta["publisher"] in {"Elsevier", "Springer"} and "copyright" in lower_text:
                return None

            return meta
        except Exception:
            # API can be flaky, don't die on one bad query
            continue

    return None
