# SmartResearch – CSIT321


**SmartResearch** is an intelligent research assistant built for automated PDF ingestion, metadata extraction, clustering, and semantic search.  
It allows researchers to **upload, summarise, and group academic papers** into topic clusters using NLP and machine learning.

---

## Repository Structure
```markdown
backend/ → FastAPI server for processing, summarisation, and search
frontend/ → React + Vite interface for upload, browsing, and clustering
docs/ → Reports, planning documents, and deliverables
data/ → Local storage for uploaded PDFs (runtime-generated)
```

---

## Current Features :) 

| Feature | Description |
|----------|--------------|
| **PDF Upload & OCR** | Uploads research papers, extracts text (OCR fallback for scanned files). |
| **Automatic Metadata Extraction** | Parses title, author, and year from document text. |
| **Summarisation Engine** | Generates text summaries using extractive + semantic methods. |
| **Clustering System** | Groups similar papers by topic using TF-IDF or embedding vectors. |
| **Semantic Search** | Allows natural-language search through all stored papers. |
| **Local Storage Layer** | Manages uploaded files, text, and metadata without an external DB. |
| **Frontend Integration** | React interface for uploading, viewing, and exploring clusters. |

---

## 🖥️System Overview

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

| Layer | Tools & Frameworks | Purpose |
|--------|--------------------|----------|
| **Frontend** | React, Vite, Tailwind CSS | Modern UI framework for upload, browsing, and clustering views. |
| **Backend** | FastAPI (Python) | Core application layer for document processing and REST endpoints. |
| **Machine Learning / NLP** | scikit-learn, SentenceTransformers (MiniLM), NumPy | Power clustering, TF-IDF vectorisation, and semantic similarity search. |
| **Text Extraction** | PyPDF2, pytesseract (OCR) | Extracts raw text from PDFs, with OCR fallback for scanned documents. |
| **Summarisation** | TextRank, semantic embeddings | Generates extractive and semantic summaries from paper text. |
| **Storage** | Local filesystem + JSON index | Lightweight document registry for offline, file-based persistence. |
| **Build & Tooling** | Uvicorn, Node.js, npm | Dev servers and runtime management for backend and frontend respectively. |
| **API Testing / Docs** | Swagger (auto-generated from FastAPI) | Provides interactive API documentation for quick validation. |






