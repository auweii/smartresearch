# SmartResearch — Models

This directory defines all **Pydantic models (schemas)** used by the SmartResearch backend.  
These schemas handle request and response validation across the FastAPI endpoints, ensuring a consistent data structure between the backend and frontend.

---

## Overview

Each file here provides data models for a specific backend domain.  
They define the input/output formats used in:
- **Upload & Storage**
- **Summarization**
- **Clustering**
- **Search & Metadata Retrieval**

The models live in `schemas.py` and are imported throughout the app:
```python
from models.schemas import UploadResponse, SearchRequest, MetaResponse
