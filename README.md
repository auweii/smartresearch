# SmartResearch – CSIT321

**SmartResearch** is an AI-assisted research tool for automated PDF ingestion, metadata extraction, clustering, and semantic search.  
It enables users to upload, summarise, and organise academic papers into interpretable topic clusters using NLP and machine learning.

---

## Repository Structure

backend/   → FastAPI backend for processing, summarisation, and search  
frontend/  → React + Vite interface for upload, browsing, and clustering  
docs/      → Reports, planning documents, and submission deliverables  
data/      → Local storage for uploaded PDFs and generated outputs  

---

## Features

| Feature | Description |
|--------|-------------|
| **PDF Upload & OCR** | Upload research papers with text extraction and OCR fallback for scanned documents. |
| **Metadata Extraction** | Automatically extracts title, authors, and year, with optional enrichment (e.g. CrossRef). |
| **Summarisation Engine** | Generates structured summaries using extractive and semantic methods. |
| **Clustering System** | Groups papers into topic clusters using TF-IDF and embedding-based methods. |
| **Search (Keyword / Semantic / Hybrid)** | Supports multiple retrieval modes for different research workflows. |
| **Semantic Similarity** | Embedding-based similarity enables related paper discovery. |
| **Local Storage** | Stores PDFs, extracted text, and metadata locally without requiring an external database. |
| **Frontend Integration** | React interface supporting upload, browsing, clustering, and export workflows. |

---

## System Capabilities

The backend implements a complete end-to-end processing pipeline for uploaded PDFs rather than isolated components.

- Extracts text from standard PDFs with OCR fallback for scanned documents  
- Generates structured summaries using both extractive and abstractive approaches  
- Automatically extracts and enriches metadata with confidence scoring  
- Embeds documents using SentenceTransformers for semantic retrieval  
- Supports keyword, semantic, and hybrid search modes  
- Clusters papers using TF-IDF and KMeans into interpretable topic groups  
- Exposes API endpoints for upload, search, clustering, summaries, and document retrieval  

The frontend integrates these endpoints into a unified workflow:

**Upload → All Papers → Cluster → Export**

All files and metadata are stored locally using a lightweight file-based persistence model.

---

## Known Issues

- The **“View Summary”** action in the All Papers view may not consistently display the correct summary data. This is currently being fixed.

## Notes

- Tested on **Python 3.11.14** (other versions may cause issues)

---

## System Overview

**Architecture:**
```markdown
  ┌────────────────┐          ┌──────────────────────┐          ┌────────────────────┐
  │ React Frontend │  ←→      │   FastAPI Backend    │  ←→      │    Local Storage   │
  └────────────────┘          └──────────────────────┘          └────────────────────┘
            │                              │
            │                              │
        Upload UI              PDF Extraction, Metadata, Search
```

---

## Quick Start

### Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate     # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
uvicorn app:app --reload
```

Backend runs at:
``http://127.0.0.1:8000``
Swagger UI: 
``http://127.0.0.1:8000/docs``

### Frontend Setup 
```bash
cd frontend
npm install
npm run dev
```

---

### Core Flow 
1. Upload PDFs → ``/upload``
2. View All Papers → ``/all``
3. Cluster Topics → ``/cluster``
4. Export or Merge Reports → ``/export``, ``/merge``

---

## Tech Stack

| Layer | Tools | Purpose |
|------|------|---------|
| **Frontend** | React, Vite, Tailwind CSS | Interface for upload, browsing, clustering, and export |
| **Backend** | FastAPI (Python) | API layer for processing and orchestration |
| **ML / NLP** | scikit-learn, SentenceTransformers, NumPy | Clustering, TF-IDF, semantic search |
| **Text Extraction** | PyPDF2, pytesseract | PDF parsing with OCR fallback |
| **Summarisation** | TextRank, embedding-based methods | Structured summary generation |
| **Storage** | Local filesystem + JSON index | Lightweight persistence |
| **Tooling** | Uvicorn, Node.js, npm | Runtime and development tooling |
| **API Docs** | Swagger (FastAPI) | Interactive API documentation |

---
