# SmartResearch — Services

This directory contains all **core processing modules** that power the SmartResearch backend.  
Each service performs a specific data-processing or ML-related task — from OCR extraction to semantic embedding and summarization — forming the functional backbone of the app’s intelligence layer.

---

## Directory Overview

| File | Purpose |
|------|----------|
| `extract.py` | Extracts raw text from PDFs via direct parsing (non-OCR). |
| `ocr.py` | Performs OCR extraction using `pdf2image` + `pytesseract` for scanned PDFs. |
| `metadata.py` | Enriches documents with bibliographic metadata using the CrossRef API. |
| `embed.py` | Creates lightweight TF-IDF embeddings for keyword search. |
| `semantic.py` | Manages transformer-based semantic embeddings using SPECTER2 and optional FAISS acceleration. |
| `cluster.py` | Wraps KMeans clustering for document vector grouping. |
| `summarize.py` | Implements lightweight extractive summarization (“TextRankish”). |
| `abstractive.py` | Runs transformer-based abstractive summarization with DistilBART. |

---

## Module Summaries

### **extract.py**
Extracts selectable text directly from a PDF using **PyPDF2**.  
Skips malformed or encrypted pages gracefully.  
Outputs a single string containing all concatenated text.  
:contentReference[oaicite:0]{index=0}

---

### **ocr.py**
Handles OCR for scanned documents using:
- `pdf2image` to render pages as images.
- `pytesseract` to perform text recognition.
Returns the combined text for all pages.  
:contentReference[oaicite:1]{index=1}

---

### **metadata.py**
Attempts to infer bibliographic metadata (title, author list, DOI, etc.)  
from early document lines via the **CrossRef API**.  
Rejects clearly non-academic content (recipes, workouts, etc.)  
and filters false positives with regex sanity checks.  
:contentReference[oaicite:2]{index=2}

---

### **embed.py**
Provides a simple **TF-IDF embedder** for fast bag-of-words representations.  
Ideal for keyword search and clustering when transformer embeddings are overkill.  
Includes:
- `fit_transform()` → train + transform corpus  
- `transform()` → vectorize new docs  
:contentReference[oaicite:3]{index=3}

---

### **semantic.py**
Implements transformer-level semantic search and document similarity using **Sentence-Transformers (SPECTER2)**.  
Supports:
- Chunk-level encoding (≈500-word blocks)  
- Optional **FAISS** acceleration  
- Persistent on-disk embedding store (`semantic_chunks.json`)  
- Functions: `add_doc()`, `remove_doc()`, `search()`, `similar()`, `ensure_loaded()`.  
Auto-initializes on import for transparent operation.  
:contentReference[oaicite:4]{index=4}

---

### **cluster.py**
Thin wrapper over **sklearn KMeans**, exposing a minimal API:  
- `fit(X)` → predict cluster labels  
- `centroids()` → return cluster centers as lists  
Used for document grouping and topic segmentation.  
:contentReference[oaicite:5]{index=5}

---

### **summarize.py**
Implements an **extractive “TextRank-like” summarizer** using sentence frequency scoring.  
Uses NLTK tokenization and stopword filtering to select the top-N most representative sentences.  
:contentReference[oaicite:6]{index=6}

---

### **abstractive.py**
Performs **abstractive summarization** via a transformer pipeline (`distilbart-cnn-12-6` by default).  
Automatically chunks long text, summarises per-chunk, and merges results with an optional “summary of summaries” step.  
Supports configurable length targets: `short`, `medium`, `long`.  
:contentReference[oaicite:7]{index=7}

---

## Design Notes
- Each service is **independent** and can be imported standalone.  
- Heavy models (e.g., SPECTER2, DistilBART) are lazily loaded on module import to minimize runtime cost.  
- All external API calls (`CrossRef`, `Semantic Scholar`) have network timeouts and safe fallbacks.  
- Extraction functions avoid crashing on malformed files — they *fail soft*.  

---

## Example Integration

```python
from services.extract import pdf_to_text
from services.metadata import enrich_from_text
from services.semantic import search

text = pdf_to_text("example.pdf")
meta = enrich_from_text(text)
hits = search("transformer architecture", topk=5)
