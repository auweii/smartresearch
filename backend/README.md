#  SmartResearch — Backend

The **SmartResearch Backend** powers document ingestion, clustering, summarization, and semantic retrieval for the SmartResearch app.  
It’s built on [FastAPI](https://fastapi.tiangolo.com/) with a modular architecture across models, services, and storage.

---

## Features

- PDF ingestion, OCR, and metadata enrichment  
- Text extraction and summarization (extractive + abstractive)  
- TF-IDF and transformer-based semantic search  
- Document clustering and topic grouping  
- Persistent local storage (filesystem-based)  
- RESTful API endpoints ready for React/Vite frontend integration  

---

##  Directory Structure
```markdown
backend/
├── app.py # FastAPI entrypoint
├── models/ # Pydantic schemas (data contracts)
├── services/ # Core ML & processing modules
├── utils/storage.py # File and metadata storage layer
├── requirements.txt # Python dependencies
└── data_store/ # Runtime-generated storage
```

---

## Run Locally

Set up a virtual environment and install dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the API with uvicorn:
```bash
uvicorn app:app --reload
```

Then open Swagger Docs:
```bash
http://localhost:8000/docs
```

---

##  Architecture

| Layer | Description |
|-------|--------------|
| **Models** | Defines all request/response schemas with Pydantic. |
| **Services** | Implements logic for text extraction, embeddings, summarization, clustering, and metadata enrichment. |
| **Storage** | Handles persistent local storage and retrieval of uploaded files, texts, and metadata. |
| **App Layer** | Exposes FastAPI endpoints and orchestrates interactions between services and storage. |

---

##  Example API Calls

### Health Check
```bash
GET /api/health
→ {"ok": true}
```
---

Upload a PDF
```bash
POST /api/upload
```
→ Returns parsed text, extracted metadata, and a short preview.

---

Semantic Search
```bash
POST /api/semantic_search
Body: {"q": "transformer models", "topk": 5}
```
→ Ranked results with document previews.
