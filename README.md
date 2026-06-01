# SmartResearch — CSIT321 Capstone Project

**SmartResearch** is an AI-assisted research-paper management tool developed for the CSIT321 capstone project.

The application allows users to upload academic PDFs, extract and enrich bibliographic metadata, generate summaries, search stored papers, explore topic clusters, retrieve related-paper recommendations, and export configurable PDF research reports.

SmartResearch is implemented as a local web-based prototype with a React frontend, a FastAPI backend, and filesystem-based persistence. It does not require an external database.

---

## Project Team

### Group Members

| Team Member        | Student Number |
| ------------------ | -------------- |
| **Chelsea Okan**   | 8438675        |
| **Noor Ahmed**     | 7295297        |
| **Nishad Gyawali** | 8124553        |

### Subject Coordinators

* Dr. John Le
* Dr. Khoa Nguyen

Detailed task allocation, repository evidence, and contribution records are preserved in:

[`docs/a6/contribution-table.pdf`](docs/a6/contribution-table.pdf)

---

## Core Workflow

```text
Upload PDFs → Review Papers → Search and Summarise → Explore Clusters → Export Report
```

| Step    | Frontend Route | Purpose                                                             |
| ------- | -------------- | ------------------------------------------------------------------- |
| Upload  | `/upload`      | Upload and preview PDF documents.                                   |
| Review  | `/papers`      | Browse stored papers, inspect metadata, search, and delete records. |
| Summary | `/papers/:id`  | Generate summaries and view related-paper recommendations.          |
| Cluster | `/cluster`     | Explore topic clusters and grouped papers.                          |
| Export  | `/export`      | Configure and download a PDF research report.                       |

---

## Features

| Feature                    | Description                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **PDF Upload**             | Upload one or more academic PDF files through drag-and-drop or file selection.                                                                                           |
| **Direct Text Extraction** | Extract selectable text from uploaded PDF documents.                                                                                                                     |
| **OCR Fallback**           | Attempt OCR for scanned or low-text PDFs when Tesseract OCR is installed separately.                                                                                     |
| **Metadata Extraction**    | Extract title, authors, year, DOI, venue, and related fields using PDF layout analysis and local parsing.                                                                |
| **Metadata Enrichment**    | Improve bibliographic metadata through CrossRef where reliable external results are available.                                                                           |
| **Extractive Summaries**   | Generate concise summaries by preferring Semantic Scholar abstracts when available via DOI, then local abstract text, with TextRank-like sentence scoring as a fallback. |
| **Abstractive Summaries**  | Generate short, medium, or long DistilBART summaries on demand with CPU fallback and optional GPU acceleration.                                                          |
| **Keyword Search**         | Perform TF-IDF keyword search across stored paper text.                                                                                                                  |
| **Semantic Search**        | Perform transformer-based semantic retrieval using chunk-level embeddings.                                                                                               |
| **Hybrid Search**          | Combine semantic and keyword-search scores for balanced relevance ranking.                                                                                               |
| **Semantic Similarity**    | Retrieve related stored papers using local embedding similarity.                                                                                                         |
| **Recommendations**        | Retrieve Semantic Scholar recommendations where available, with local similarity fallback.                                                                               |
| **Topic Clustering**       | Group papers using adaptive KMeans clustering with silhouette-scored cluster selection, TF-IDF keyword labels, and outlier handling.                                     |
| **Paper Management**       | Browse metadata, inspect summaries, delete individual records, or clear displayed papers.                                                                                |
| **PDF Export**             | Generate configurable reports containing selected papers, metadata, summaries, clusters, keywords, charts, and optional recommendations.                                 |
| **Local Storage**          | Store uploaded PDFs, extracted text, metadata, and semantic embeddings locally without an external database.                                                             |

---

## Repository Structure

```text
smartresearch/
├── backend/                    # FastAPI backend, processing services, and local storage
│   ├── app.py                  # API entry point
│   ├── models/                 # Pydantic request and response schemas
│   ├── services/               # Extraction, OCR, metadata, summaries, search, and clustering
│   ├── utils/                  # Filesystem-based storage utility
│   ├── requirements.txt        # Standard dependency set
│   ├── requirements-gpu.txt    # Optional NVIDIA GPU dependency set
│   └── data_store/             # Runtime-generated local persistence
├── frontend/                   # React, Vite, and Tailwind CSS frontend
│   ├── public/                 # Static public assets
│   ├── src/                    # Components, pages, routing, styles, and API helpers
│   ├── package.json            # Frontend scripts and dependencies
│   └── README.md               # Frontend documentation
├── docs/                       # Assignment archives and supporting documentation
│   ├── a1/                     # Assignment 1 archive
│   ├── a2/                     # Assignment 2 archive
│   ├── a3/                     # Assignment 3 archive
│   ├── a4/                     # Assignment 4 archive
│   ├── a5/                     # Assignment 5 archive
│   ├── a6/                     # Final Assignment 6 documentation archive
│   ├── acceptance-criteria/    # Milestone-specific acceptance snapshots
│   ├── diagrams/               # Final technical diagrams
│   ├── weekly-meeting-minutes/ # Formal and asynchronous meeting records
│   └── risk_register.md        # Project risk register
└── README.md                   # Repository overview
```

The `backend/data_store/` directory is created automatically at runtime.

---

## System Requirements

### Required

* Python 3.10 recommended
* Node.js `20.19+` or `22.12+`
* npm
* Internet access during the initial model download
* Internet access for optional CrossRef and Semantic Scholar requests

### Required Only for OCR Fallback

Tesseract OCR must be installed separately for scanned or low-text PDF support.

The Python package `pytesseract` is included in both backend dependency files, but `pytesseract` is only a Python wrapper.

Installing either of the following files does **not** install the Tesseract OCR executable:

```text
requirements.txt
requirements-gpu.txt
```

The Tesseract executable must be installed separately and made available on the system `PATH`.

#### Windows

Install Tesseract OCR using the Windows installer:

```text
https://github.com/UB-Mannheim/tesseract/wiki
```

Add the Tesseract installation directory to the system `PATH`.

#### macOS

```bash
brew install tesseract
```

#### Linux

```bash
sudo apt install tesseract-ocr
```

Direct PDF extraction still works without Tesseract.

OCR fallback is unavailable until the Tesseract executable is installed separately.

### Optional NVIDIA GPU Acceleration

An NVIDIA GPU is not required to run SmartResearch.

The standard dependency set works on non-CUDA systems and automatically falls back to CPU execution for transformer-based abstractive summaries.

For optional GPU acceleration, use `requirements-gpu.txt` instead of `requirements.txt`.

A compatible NVIDIA GPU and driver are required.

A separate CUDA toolkit installation is not required for standard use.

---

## Quick Start

Start the backend before opening the frontend.

### 1. Start the Backend

#### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

#### macOS or Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

> **OCR Note:** Installing the Python dependencies does not install the Tesseract OCR executable. Install Tesseract separately only when scanned-PDF or OCR-fallback support is required.

The backend runs at:

```text
http://127.0.0.1:8000
```

The interactive Swagger API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### 2. Optional NVIDIA GPU Setup

Use this dependency file instead of `requirements.txt` on a supported NVIDIA setup:

```bash
cd backend
pip install -r requirements-gpu.txt
uvicorn app:app --reload
```

The GPU dependency file installs the CUDA-enabled PyTorch dependency set.

### 3. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend at:

```text
http://localhost:5173
```

---

## Frontend Route Map

| Route         | Component       | Purpose                                                                         |
| ------------- | --------------- | ------------------------------------------------------------------------------- |
| `/`           | Redirect        | Redirects users to `/upload`.                                                   |
| `/upload`     | `UploadPage`    | Uploads, tracks, and previews PDFs.                                             |
| `/papers`     | `AllPapersPage` | Browses, searches, inspects, and deletes stored papers.                         |
| `/papers/:id` | `FullSummary`   | Displays detailed metadata, generates summaries, and retrieves recommendations. |
| `/cluster`    | `ClusterPage`   | Displays topic clusters and grouped papers.                                     |
| `/export`     | `ExportPage`    | Configures and downloads PDF reports.                                           |

---

## Core API Endpoints

### Document Management

| Method   | Endpoint               | Purpose                                           |
| -------- | ---------------------- | ------------------------------------------------- |
| `GET`    | `/api/health`          | Returns a basic backend health check.             |
| `GET`    | `/api/docs`            | Lists uploaded documents and available summaries. |
| `POST`   | `/api/upload`          | Uploads and processes a PDF document.             |
| `DELETE` | `/api/docs/{doc_id}`   | Deletes a document and its related local data.    |
| `GET`    | `/api/text/{doc_id}`   | Returns extracted document text.                  |
| `GET`    | `/api/meta/{doc_id}`   | Returns stored and enriched metadata.             |
| `GET`    | `/files/{file_id}.pdf` | Serves a stored PDF file.                         |

### Search and Clustering

| Method | Endpoint                | Purpose                                                      |
| ------ | ----------------------- | ------------------------------------------------------------ |
| `POST` | `/api/search`           | Performs TF-IDF keyword search.                              |
| `POST` | `/api/semantic_search`  | Performs transformer-based semantic search.                  |
| `POST` | `/api/hybrid_search`    | Combines semantic and keyword-search scores.                 |
| `GET`  | `/api/similar/{doc_id}` | Returns locally stored papers with similar semantic content. |
| `GET`  | `/api/clustered`        | Returns generated document clusters and topic keywords.      |
| `POST` | `/api/reindex`          | Rebuilds semantic embeddings for stored documents.           |
| `POST` | `/api/move_to_storage`  | Returns the status of documents registered in local storage. |

### Summaries, Recommendations, and Export

| Method  | Endpoint                             | Purpose                                                         |
| ------- | ------------------------------------ | --------------------------------------------------------------- |
| `POST`  | `/api/summarize/{doc_id}`            | Generates an abstractive summary.                               |
| `PATCH` | `/api/meta/{doc_id}/summary`         | Saves an edited or generated summary.                           |
| `PATCH` | `/api/meta/{doc_id}/recover_summary` | Restores the original extractive summary.                       |
| `GET`   | `/api/external_recs/{doc_id}`        | Retrieves Semantic Scholar recommendations with local fallback. |
| `POST`  | `/api/export`                        | Generates a configurable PDF research report.                   |
| `GET`   | `/api/system/gpu`                    | Reports whether CUDA acceleration is available.                 |

---

## Local Storage

SmartResearch uses filesystem-based local persistence rather than an external database.

By default, runtime data is stored under:

```text
backend/data_store/
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
| `texts/`               | Stores extracted text and metadata JSON files.                  |
| `index.json`           | Stores the local document registry.                             |
| `semantic_chunks.json` | Stores persistent semantic embeddings and document lookup data. |

`semantic_chunks.json` persists across backend restarts and is updated automatically when papers are uploaded or deleted.

Use `POST /api/reindex` to rebuild semantic embeddings manually when required.

A custom storage location can be configured using the `SMARTRESEARCH_DATA` environment variable.

---

## Data Store Management

### Standard Cleanup

For normal use, delete papers through the frontend.

The All Papers page supports individual deletion and bulk deletion of displayed records.

Using the application controls keeps uploaded files, extracted text, metadata, index records, and semantic embeddings aligned.

### Full Development Reset

Stop the backend before manually deleting the runtime store.

#### Windows PowerShell

Run from the repository root:

```powershell
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .\backend\data_store
```

#### macOS or Linux

Run from the repository root:

```bash
rm -rf backend/data_store
```

Restart the backend afterward.

The storage directories will be created again automatically.

### Rebuild the Semantic Index

To rebuild semantic embeddings while preserving stored documents:

#### Windows PowerShell

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/reindex -Method POST
```

#### macOS or Linux

```bash
curl -X POST http://127.0.0.1:8000/api/reindex
```

---

## Technology Stack

| Layer                 | Technologies                                                        | Purpose                                                     |
| --------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Frontend**          | React, Vite, Tailwind CSS, React Router DOM, Axios                  | User interface, routing, styling, and backend communication |
| **PDF Preview**       | React PDF Viewer                                                    | Completed-upload PDF preview                                |
| **Backend**           | FastAPI, Uvicorn, Pydantic                                          | API layer, validation, and orchestration                    |
| **Text Extraction**   | PyPDF2, PyMuPDF, Pytesseract                                        | Direct extraction and OCR fallback                          |
| **Metadata**          | PyMuPDF layout analysis, CrossRef API                               | Bibliographic extraction and enrichment                     |
| **Summarisation**     | NLTK, Semantic Scholar abstracts, TextRank-like scoring, DistilBART | Extractive and abstractive summaries                        |
| **Search**            | TF-IDF, Sentence Transformers, SPECTER2                             | Keyword, semantic, and hybrid retrieval                     |
| **Clustering**        | scikit-learn KMeans, silhouette scoring, cosine similarity          | Adaptive topic clustering and outlier handling              |
| **Recommendations**   | Semantic Scholar API, local semantic similarity                     | Related-paper discovery                                     |
| **Export**            | ReportLab                                                           | PDF research-report generation                              |
| **Storage**           | Local filesystem and JSON                                           | Lightweight persistence without an external database        |
| **API Documentation** | FastAPI Swagger UI                                                  | Interactive endpoint documentation                          |

---

## System Overview

```text
React + Vite Frontend
        │
        ▼
FastAPI Backend
        │
        ├── PDF Extraction and OCR Fallback
        ├── Metadata Extraction and CrossRef Enrichment
        ├── Extractive and Abstractive Summarisation
        ├── Keyword, Semantic, and Hybrid Search
        ├── Topic Clustering and Recommendations
        └── PDF Report Generation
        │
        ▼
Local Filesystem Storage
```

CrossRef and Semantic Scholar are optional external services.

The core document-processing and storage workflow remains local.

Generated PDF reports are returned to the browser as downloadable files and are not stored permanently under `backend/data_store/`.

---

## Documentation

| Location                                                                   | Purpose                                                                     |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [`backend/README.md`](backend/README.md)                                   | Detailed backend architecture, setup, endpoints, and storage documentation. |
| [`backend/models/README.md`](backend/models/README.md)                     | Pydantic schema documentation.                                              |
| [`backend/services/README.md`](backend/services/README.md)                 | Processing-service documentation.                                           |
| [`backend/utils/README.md`](backend/utils/README.md)                       | Filesystem-storage utility documentation.                                   |
| [`frontend/README.md`](frontend/README.md)                                 | Detailed frontend setup, routes, and workflow documentation.                |
| [`frontend/src/README.md`](frontend/src/README.md)                         | Frontend source architecture.                                               |
| [`frontend/src/components/README.md`](frontend/src/components/README.md)   | Reusable frontend-component documentation.                                  |
| [`frontend/src/pages/README.md`](frontend/src/pages/README.md)             | Page-level workflow documentation.                                          |
| [`docs/README.md`](docs/README.md)                                         | Documentation archive index.                                                |
| [`docs/acceptance-criteria/README.md`](docs/acceptance-criteria/README.md) | Assignment-specific acceptance snapshots.                                   |
| [`docs/diagrams/README.md`](docs/diagrams/README.md)                       | Final technical-diagram index.                                              |
| [`docs/risk_register.md`](docs/risk_register.md)                           | Project risk register and closeout record.                                  |
| [`docs/a6/README.md`](docs/a6/README.md)                                   | Final Assignment 6 documentation archive.                                   |
| [`docs/a6/technical-report-link.txt`](docs/a6/technical-report-link.txt)   | Repository-accessible link to the final technical report.                   |

---

## Prototype Scope and Limitations

SmartResearch is a completed local capstone prototype rather than a production-hosted platform.

The following items remain outside the submitted prototype scope:

* Authentication and user accounts
* Role-based permissions
* Cloud persistence
* Production deployment
* Multi-user collaboration
* Enterprise security controls
* Production-scale corpus handling
* Full automated regression testing
* Non-English document support
* Mobile or native applications

PDF is the supported final report-export format.

CSV and JSON remain deferred.

---

## Repository Restoration Note

The source-code ZIP submitted through the Moodle assessment portal before the Assignment 6 deadline represents the final evaluation copy of the implementation.

A late pre-submission repository update overwrote recent documentation and repository-organisation work completed during the final week.

The missing documentation was recovered from a local backup and restored after submission.

This repository may therefore include post-submission README updates, archive notes, and documentation-structure restoration.

These amendments improve repository traceability and handover clarity without altering the official submitted evaluation copy.

Further details, including the timestamped repository-evidence snapshot and post-snapshot addendum, are recorded in the Moodle submission notes and the submitted contribution table.
