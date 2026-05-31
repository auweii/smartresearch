# SmartResearch — Models

This directory contains the **Pydantic models (schemas)** defined for the SmartResearch backend.
These schemas provide structured request and response formats for the FastAPI application, helping maintain consistent data handling between the backend and frontend.

---

## Overview

The models are defined in `schemas.py` and cover:

* **Document Upload and Metadata**
* **Text Retrieval**
* **Keyword, Semantic, and Hybrid Search**
* **Clustering**
* **Extractive and Abstractive Summarisation**

The schemas currently imported by the FastAPI application include:

```python
from models.schemas import (
    FullMetadata,
    UploadResponse,
    DocMeta,
    SearchRequest,
    SearchResponse,
    SearchHit,
    MetaResponse,
    TextResponse,
)
```

Additional schemas for clustering and summarisation are also defined in `schemas.py` for future endpoint integration and extension.
