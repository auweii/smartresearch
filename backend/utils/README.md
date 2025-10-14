# SmartResearch — Storage Utility

This module handles **persistent storage and retrieval** for all uploaded files, extracted text, and metadata in the SmartResearch backend.  
It’s the backbone of the local document index, managing the filesystem-based data store and providing fast lookups without a full database.

---

## Overview

| Function | Purpose |
|-----------|----------|
| `save_file()` | Save uploaded PDFs to disk and register them in the index. |
| `save_text()` | Store processed or extracted plain text for a document. |
| `get_text()` | Retrieve stored text by document ID. |
| `save_meta()` | Write document metadata (title, authors, DOI, etc.) as JSON. |
| `get_meta()` | Load metadata JSON if it exists. |
| `get_doc()` | Fetch the index record for a specific document ID. |
| `list_docs()` | Return a list of all stored documents (newest first). |
| `delete_doc()` | Remove a document and all related data from disk. |

---

## File Structure
```markdown
data_store/
├── files/
│ ├── <id>_<filename>.pdf
├── texts/
│ ├── <id>.txt
│ ├── <id>.meta.json
└── index.json
```

Each document ID (e.g. `c8a4f8e3c9b1`) acts as a unique key for its file, extracted text, and metadata.  
The `index.json` file serves as the global registry for all stored items.

---

## Internal Mechanics

- Uses **`uuid.uuid4()`** to generate unique document IDs.  
- Hashes every uploaded file with **SHA-1** for integrity and deduplication checks.  
- Maintains an **in-memory cache** (`_index`) for fast read operations.  
- Automatically creates all storage directories on import.  
- Index changes are written back to disk immediately via `_save_index()`.  

---

## Helper Functions

| Function | Description |
|-----------|-------------|
| `_new_id()` | Creates a random short 12-character ID. |
| `_sha1()` | Returns a SHA-1 hash for byte data. |
| `_save_index()` | Serializes `_index` to `index.json`. |
| `_load_index()` | Loads `index.json` into memory at startup. |

---

## Lifecycle

1. **Upload** → `save_file()` stores the PDF and logs metadata.  
2. **Process** → `save_text()` + `save_meta()` save derived data.  
3. **Search/Cluster** → `get_text()` and `get_meta()` feed the pipeline.  
4. **Delete** → `delete_doc()` removes all traces safely.  

---

## Example Usage

```python
from utils.storage import save_file, get_text, list_docs

with open("example.pdf", "rb") as f:
    rec = save_file("example.pdf", f.read())

print(rec)           # {'id': 'c8a4f8e3c9b1', 'name': 'example.pdf', ...}
print(list_docs())   # list of all indexed docs
print(get_text(rec['id']))  # returns extracted text
