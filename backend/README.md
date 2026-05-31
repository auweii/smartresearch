# SmartResearch — Backend

The **SmartResearch Backend** powers document ingestion, metadata enrichment, summarisation, clustering, search, recommendations, and PDF export for the SmartResearch application.

It is built with [FastAPI](https://fastapi.tiangolo.com/) and follows a modular architecture across models, services, and storage utilities.

---

## Features

* PDF upload and persistent local storage
* Direct PDF text extraction with OCR fallback
* Bibliographic metadata extraction and CrossRef enrichment
* Extractive and abstractive summarisation
* TF-IDF keyword search
* Transformer-based semantic search
* Hybrid keyword and semantic search
* Similar-document discovery
* Semantic Scholar recommendations with local fallback
* Adaptive KMeans clustering with topic keywords
* Configurable PDF report export
* Interactive Swagger API documentation

---

## Directory Structure

```text
backend/
├── app.py                  # FastAPI application and API endpoints
├── models/
│   ├── README.md           # Documentation for Pydantic schemas
│   └── schemas.py          # Request and response data models
├── services/
│   ├── README.md           # Documentation for processing services
│   ├── extract.py          # Direct PDF text extraction
│   ├── ocr.py              # OCR fallback for scanned PDFs
│   ├── metadata.py         # Local metadata extraction and CrossRef enrichment
│   ├── metadata_compare.py # Metadata confidence and reliability checks
│   ├── embed.py            # Reusable TF-IDF embedding utility
│   ├── semantic.py         # Semantic embeddings and similarity search
│   ├── cluster.py          # Adaptive KMeans clustering
│   ├── summarize.py        # Extractive summarisation
│   └── abstractive.py      # DistilBART abstractive summarisation
├── utils/
│   ├── README.md           # Documentation for the storage utility
│   └── storage.py          # Filesystem-based persistence layer
├── requirements.txt        # Standard Python dependencies
├── requirements-gpu.txt    # Optional CUDA-enabled dependencies for NVIDIA GPUs
└── data_store/             # Runtime-generated local storage
```

The `data_store/` directory is created automatically at runtime.

A custom storage location can be configured using the `SMARTRESEARCH_DATA` environment variable.

---

## System Requirements

* Python 3.10 recommended
* Tesseract OCR installed system-wide for scanned PDF support
* An NVIDIA GPU is optional and only required for CUDA-accelerated abstractive summarisation

SmartResearch runs on non-CUDA systems using the standard dependency file.

---

## System Dependency: Tesseract OCR

The Python package `pytesseract` is included in both requirements files, but it is only a wrapper around the Tesseract OCR executable.

Tesseract must be installed separately and available on the system `PATH` for scanned PDF support.

### Windows

Install Tesseract OCR using the [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki), then add the installation directory to the system `PATH`.

### macOS

```bash
brew install tesseract
```

### Linux

```bash
sudo apt install tesseract-ocr
```

Direct PDF extraction still works without Tesseract.
Tesseract is only required when OCR fallback is needed for scanned or poorly extracted documents.

---

## Run Locally

Create and activate a virtual environment.

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Install one of the available dependency sets.

### Standard Installation

Use the standard dependency file for CPU-based execution:

```bash
pip install -r requirements.txt
```

This installation works on systems without an NVIDIA GPU.

Transformer-based abstractive summarisation automatically falls back to CPU execution when CUDA is unavailable.

### NVIDIA GPU Installation

For optional CUDA-enabled acceleration on supported NVIDIA hardware, install the GPU dependency set instead:

```bash
pip install -r requirements-gpu.txt
```

The GPU dependency file installs the CUDA 12.4 build of PyTorch.

A compatible NVIDIA GPU and driver are required for GPU acceleration.
A separate CUDA toolkit installation is not required for standard use.

---

## Start the Backend

Run the FastAPI server with Uvicorn:

```bash
uvicorn app:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Open the interactive Swagger documentation at:

```text
http://127.0.0.1:8000/docs
```

---

## Architecture

| Layer         | Description                                                                                                      |
| ------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Models**    | Defines Pydantic schemas for structured request and response data.                                               |
| **Services**  | Implements PDF extraction, OCR, metadata enrichment, summarisation, semantic embeddings, search, and clustering. |
| **Storage**   | Stores uploaded files, extracted text, metadata JSON, and the local document index.                              |
| **App Layer** | Exposes FastAPI endpoints and orchestrates interactions between services and storage utilities.                  |

---

## Storage Structure

Runtime data is stored under `data_store/` by default.

```text
data_store/
├── files/
│   └── <id>_<filename>
├── texts/
│   ├── <id>.txt
│   └── <id>.meta.json
├── index.json
└── semantic_chunks.json
```

| File or Directory      | Purpose                                                         |
| ---------------------- | --------------------------------------------------------------- |
| `files/`               | Stores uploaded PDF files.                                      |
| `texts/`               | Stores extracted text and document metadata JSON.               |
| `index.json`           | Stores the local document registry.                             |
| `semantic_chunks.json` | Stores persistent semantic embeddings and document lookup data. |

---

## Core API Endpoints

### Document Management

| Method   | Endpoint               | Purpose                                           |
| -------- | ---------------------- | ------------------------------------------------- |
| `GET`    | `/api/health`          | Returns a basic backend health check.             |
| `GET`    | `/api/docs`            | Lists uploaded documents and available summaries. |
| `POST`   | `/api/upload`          | Uploads and processes a PDF document.             |
| `DELETE` | `/api/docs/{doc_id}`   | Deletes a document and its stored data.           |
| `GET`    | `/api/text/{doc_id}`   | Returns extracted document text.                  |
| `GET`    | `/api/meta/{doc_id}`   | Returns stored and enriched metadata.             |
| `GET`    | `/files/{file_id}.pdf` | Serves a stored PDF file.                         |

### Search and Recommendations

| Method | Endpoint                      | Purpose                                                                    |
| ------ | ----------------------------- | -------------------------------------------------------------------------- |
| `POST` | `/api/search`                 | Performs TF-IDF keyword search.                                            |
| `POST` | `/api/semantic_search`        | Performs transformer-based semantic search.                                |
| `POST` | `/api/hybrid_search`          | Combines semantic and keyword-search scores.                               |
| `GET`  | `/api/similar/{doc_id}`       | Returns locally stored documents with similar semantic content.            |
| `GET`  | `/api/external_recs/{doc_id}` | Returns Semantic Scholar recommendations with a local similarity fallback. |

### Clustering and Indexing

| Method | Endpoint               | Purpose                                                                |
| ------ | ---------------------- | ---------------------------------------------------------------------- |
| `GET`  | `/api/clustered`       | Returns generated document clusters and topic keywords.                |
| `POST` | `/api/reindex`         | Rebuilds semantic embeddings for stored documents.                     |
| `POST` | `/api/move_to_storage` | Returns the status of documents currently registered in local storage. |

### Summarisation

| Method  | Endpoint                             | Purpose                                          |
| ------- | ------------------------------------ | ------------------------------------------------ |
| `POST`  | `/api/summarize/{doc_id}`            | Generates an abstractive summary for a document. |
| `PATCH` | `/api/meta/{doc_id}/summary`         | Saves an edited or generated document summary.   |
| `PATCH` | `/api/meta/{doc_id}/recover_summary` | Restores the original extractive summary.        |

### Export and System Information

| Method | Endpoint          | Purpose                                             |
| ------ | ----------------- | --------------------------------------------------- |
| `POST` | `/api/export`     | Generates a configurable PDF research report.       |
| `GET`  | `/api/system/gpu` | Reports whether CUDA GPU acceleration is available. |

---

## Example API Calls

### Health Check

```bash
GET /api/health
```

```json
{
  "ok": true
}
```

---

### Upload a PDF

```bash
POST /api/upload
```

Upload the PDF as multipart form data using the `file` field.

The response includes:

* Basic document metadata
* A short extracted-text preview
* Whether OCR fallback was used
* Extracted and enriched bibliographic metadata

---

### Keyword Search

```bash
POST /api/search
```

```json
{
  "q": "transformer models",
  "topk": 5
}
```

---

### Semantic Search

```bash
POST /api/semantic_search
```

```json
{
  "q": "transformer models",
  "topk": 5
}
```

---

### Hybrid Search

```bash
POST /api/hybrid_search
```

```json
{
  "q": "transformer models",
  "topk": 5
}
```

---

### Generate an Abstractive Summary

```bash
POST /api/summarize/{doc_id}?target=medium
```

Supported summary targets:

* `short`
* `medium`
* `long`

---

### Export a PDF Report

```bash
POST /api/export
```

The export endpoint generates a PDF report containing selected papers, metadata, summaries, clusters, keywords, and optional analytics charts.

---

## Notes

* Direct PDF extraction is attempted before OCR fallback.
* OCR uses PyMuPDF page rendering and Pytesseract text recognition.
* Semantic embeddings use SPECTER2 by default with a MiniLM fallback.
* Semantic embeddings persist across backend restarts.
* Abstractive summarisation uses DistilBART and automatically selects GPU or CPU execution.
* Keyword, semantic, and hybrid search are exposed as separate API endpoints.
* Uploaded files, extracted text, metadata, and embeddings are stored locally without requiring an external database.
