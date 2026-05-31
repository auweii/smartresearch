# SmartResearch — Services

This directory contains the core processing modules used by the SmartResearch backend.
Each service handles a specific document-processing, metadata, search, clustering, or summarisation task.

---

## Directory Overview

| File                  | Purpose                                                                                                                     |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `extract.py`          | Extracts selectable text directly from PDF files using PyMuPDF.                                                             |
| `ocr.py`              | Renders PDF pages as images with PyMuPDF and performs OCR using Pytesseract.                                                |
| `metadata.py`         | Extracts local bibliographic metadata and enriches it through the CrossRef API.                                             |
| `metadata_compare.py` | Compares locally extracted metadata against CrossRef results and calculates confidence and reliability values.              |
| `embed.py`            | Provides a reusable TF-IDF vectoriser wrapper for lightweight text embeddings.                                              |
| `semantic.py`         | Manages transformer-based semantic embeddings, document similarity, and persistent embedding storage.                       |
| `cluster.py`          | Groups document embeddings using adaptive KMeans clustering with outlier handling.                                          |
| `summarize.py`        | Generates extractive summaries using Semantic Scholar abstracts, local abstract extraction, and sentence-frequency scoring. |
| `abstractive.py`      | Generates transformer-based abstractive summaries using DistilBART.                                                         |

---

## Module Summaries

### `extract.py`

Extracts selectable text directly from PDF files using **PyMuPDF**.
Pages that cannot be parsed are skipped individually, allowing text extraction to continue where possible.

---

### `ocr.py`

Provides an OCR fallback for scanned or poorly extracted PDF files.
Each PDF page is rendered as an image using **PyMuPDF** and processed with **Pytesseract**.

The upload pipeline uses this fallback when direct extraction produces insufficient usable text.

---

### `metadata.py`

Extracts bibliographic metadata from uploaded documents, including:

* Title
* Author list
* DOI
* Publication year
* Venue
* Publisher

The service uses document layout and early text content to identify local metadata, then queries the **CrossRef API** for enrichment when a plausible title is available.

---

### `metadata_compare.py`

Compares locally extracted metadata against CrossRef results.
The comparison considers title similarity, author similarity, and publication year alignment.

The service returns:

* Matched external metadata
* Confidence score
* Reliability status

---

### `embed.py`

Provides a lightweight **TF-IDF** embedding utility built around `sklearn.feature_extraction.text.TfidfVectorizer`.

The `Embedder` class exposes:

* `fit_transform()` to fit and vectorise a document collection
* `transform()` to vectorise additional text using the fitted vocabulary

The current FastAPI keyword-search endpoint maintains its own TF-IDF cache directly in `app.py`, while this module remains available as a reusable utility.

---

### `semantic.py`

Implements semantic search and document similarity using **Sentence-Transformers**.

The default embedding model is:

```text
allenai/specter2_base
```

If the default model cannot be loaded, the service falls back to:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The service:

* Splits documents into approximately 800-word chunks
* Generates normalised transformer embeddings
* Stores embeddings in `semantic_chunks.json`
* Supports persistent reloads across backend restarts
* Calculates similarity using NumPy vector operations
* Provides `add_doc()`, `remove_doc()`, `search()`, `similar()`, and `ensure_loaded()`

The embedding model is loaded when the module is imported.

---

### `cluster.py`

Groups document-level semantic embeddings using **scikit-learn KMeans**.

The clustering service:

* Selects an appropriate cluster count using silhouette scoring
* Assigns documents to generated clusters
* Marks low-similarity documents as outliers
* Moves singleton clusters into the outlier group
* Exposes cluster centroids when needed

---

### `summarize.py`

Generates extractive summaries through a layered fallback process.

The service:

1. Retrieves a Semantic Scholar abstract when a DOI is available
2. Extracts a local abstract from the document when possible
3. Falls back to sentence-frequency scoring across the document body

The fallback summariser uses **NLTK** tokenisation and stopword filtering to identify representative sentences while removing common metadata and formatting noise.

---

### `abstractive.py`

Generates abstractive summaries using the transformer model:

```text
sshleifer/distilbart-cnn-12-6
```

The model is loaded lazily when abstractive summarisation is first requested.

The service:

* Supports `short`, `medium`, and `long` targets
* Splits long documents into word-based chunks
* Summarises each chunk independently
* Merges chunk summaries into a final summary when necessary
* Uses GPU acceleration automatically when CUDA is available

---

## Design Notes

* Direct PDF extraction is attempted before OCR fallback is used.
* Semantic embeddings are stored on disk and can be rebuilt through the backend reindex endpoint.
* Transformer-based semantic embeddings use SPECTER2 with a MiniLM fallback.
* Abstractive summarisation loads DistilBART only when requested.
* CrossRef and Semantic Scholar API requests use timeouts and fallback behaviour.
* Keyword, semantic, and hybrid search are exposed separately by the FastAPI backend.

---

## Example Integration

```python
from services.extract import pdf_to_text
from services.metadata import enrich_from_text
from services.semantic import add_doc, search

pdf_path = "example.pdf"
doc_id = "example"

text = pdf_to_text(pdf_path)
meta = enrich_from_text(text, pdf_path)

add_doc(doc_id, text)
hits = search("transformer architecture", topk=5)
```
