# SmartResearch – CSIT321

**SmartResearch** is an AI-assisted research tool for automated PDF ingestion, metadata extraction, clustering, and semantic search.  
It enables users to upload, summarise, and organise academic papers into interpretable topic clusters using NLP and machine learning.

---

## Repository Structure

```
backend/   → FastAPI backend for processing, summarisation, and search
frontend/  → React + Vite interface for upload, browsing, and clustering
docs/      → Reports, planning documents, and submission deliverables
data/      → Local storage for uploaded PDFs and generated outputs
```

---

## Features

| Feature | Description |
|--------|-------------|
| **PDF Upload & OCR** | Upload research papers with text extraction and automatic OCR fallback for scanned or image-rendered documents. |
| **Metadata Extraction** | Automatically extracts title, authors, year, DOI, and venue using font-size analysis and CrossRef enrichment. |
| **Summary Engine** | Generates structured summaries using extractive (TextRank-like) methods, preferring Semantic Scholar abstracts when available via DOI. |
| **AI Summary** | On-demand abstractive summarization using DistilBART — GPU-accelerated on NVIDIA hardware, CPU fallback otherwise. |
| **Clustering System** | Groups papers into topic clusters using KMeans with silhouette-scored k selection and outlier detection. |
| **Search (Keyword / Semantic / Hybrid)** | Supports TF-IDF keyword, SPECTER2 semantic, and hybrid search modes. |
| **Semantic Similarity** | Chunk-level SPECTER2 embeddings enable related paper discovery across the corpus. |
| **Local Storage** | Stores PDFs, extracted text, metadata, and embeddings locally without requiring an external database. |
| **Frontend Integration** | React interface supporting upload, browsing, clustering, and export workflows. |

---

## System Requirements

### All Users
- Python 3.10 (tested — other versions may cause issues)
- Node.js 18+
- **Tesseract OCR** — required for scanned PDF support, must be installed system-wide:
  - **Windows:** Download installer from https://github.com/UB-Mannheim/tesseract/wiki and add to PATH
  - **macOS:** `brew install tesseract`
  - **Linux:** `sudo apt install tesseract-ocr`

### GPU Users (Optional — for faster AI summaries)
- NVIDIA GPU with CUDA toolkit installed system-wide (https://developer.nvidia.com/cuda-downloads)
- Use `requirements-gpu.txt` instead of `requirements.txt` (see GPU Setup below)

---



**Upload → All Papers → Cluster → Export**

All files and metadata are stored locally using a lightweight file-based persistence model.

---

## Quick Start
> **Note:** The backend must be running before opening the frontend.


### Backend Setup (GPU — NVIDIA only)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-gpu.txt
uvicorn app:app
```

Backend runs at: `http://127.0.0.1:8000`  
Swagger UI: `http://127.0.0.1:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Core Flow

1. Upload PDFs → `/upload`
2. View All Papers → `/papers`
3. Cluster Topics → `/cluster`
4. Export Report → `/export`

---


## Data Store Management (Development)

To clear all uploaded documents, preserving semantic index:
```powershell
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue C:\Users\nisha\smartresearch\backend\data_store\files\*
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue C:\Users\nisha\smartresearch\backend\data_store\texts\*
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue C:\Users\nisha\smartresearch\backend\data_store\meta\*
Remove-Item -Force -ErrorAction SilentlyContinue C:\Users\nisha\smartresearch\backend\data_store\index.json
```

> **Note:** Do not delete `semantic_chunks.json` unless doing a full reset. The semantic index persists across restarts and is updated automatically on upload and delete.

To manually reindex semantic search after a full reset:
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/reindex -Method POST
```

---

## Tech Stack

| Layer | Tools | Purpose |
|------|------|---------|
| **Frontend** | React, Vite, Tailwind CSS | Interface for upload, browsing, clustering, and export |
| **Backend** | FastAPI (Python) | API layer for processing and orchestration |
| **ML / NLP** | scikit-learn, SentenceTransformers, NumPy | Clustering, TF-IDF, semantic search |
| **Embeddings** | allenai/specter2_base | Academic document semantic embeddings |
| **Text Extraction** | PyMuPDF (fitz), pytesseract | PDF parsing with OCR fallback |
| **Summarisation** | TextRank-like extractive, DistilBART abstractive | Structured summary generation |
| **Metadata** | CrossRef API, Semantic Scholar API | Bibliographic enrichment and abstract retrieval |
| **Storage** | Local filesystem + JSON index | Lightweight persistence |
| **Tooling** | Uvicorn, Node.js, npm | Runtime and development tooling |
| **API Docs** | Swagger (FastAPI) | Interactive API documentation |

---

## System Overview

**React Frontend** communicates with the **FastAPI Backend**, which reads and writes to **Local Storage**.

The frontend handles user interaction and display. The backend handles PDF extraction, metadata enrichment, summarisation, search, clustering, and embedding generation. All outputs are stored locally on the file system.