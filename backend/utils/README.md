# SmartResearch — Storage Utility

This module handles persistent filesystem-based storage and retrieval for uploaded files, extracted text, and document metadata in the SmartResearch backend.
It maintains the local document index and provides lightweight storage operations without requiring a database.

---

## Overview

| Function       | Purpose                                                                  |
| -------------- | ------------------------------------------------------------------------ |
| `save_file()`  | Stores an uploaded file on disk and registers it in the document index.  |
| `save_text()`  | Stores processed or extracted plain text for a document.                 |
| `get_text()`   | Retrieves stored text by document ID.                                    |
| `save_meta()`  | Stores document metadata as JSON.                                        |
| `get_meta()`   | Loads stored metadata JSON when available.                               |
| `get_doc()`    | Retrieves the index record for a specific document ID.                   |
| `list_docs()`  | Returns a list of stored documents with basic metadata.                  |
| `delete_doc()` | Removes a document file, extracted text, metadata, and its index record. |

---

## Storage Location

By default, runtime data is stored under:

```text id="n0oiv2"
data_store/
```

A custom storage directory can be configured using the `SMARTRESEARCH_DATA` environment variable.

---

## File Structure

```text id="7d0zvk"
data_store/
├── files/
│   └── <id>_<filename>
├── texts/
│   ├── <id>.txt
│   └── <id>.meta.json
└── index.json
```

Each document is assigned a short unique ID, such as:

```text id="g0of13"
c8a4f8e3c9b1
```

The ID links the uploaded file, extracted text, metadata JSON, and index record.

The `index.json` file acts as the registry for stored documents.

---

## Stored Index Records

When a file is saved, the storage utility records:

| Field     | Description                                      |
| --------- | ------------------------------------------------ |
| `id`      | Randomly generated 12-character document ID.     |
| `name`    | Original uploaded filename.                      |
| `path`    | Filesystem path to the stored file.              |
| `bytes`   | File size in bytes.                              |
| `sha1`    | SHA-1 hash of the uploaded file contents.        |
| `created` | Unix timestamp recorded when the file is stored. |

The SHA-1 value is stored as file metadata and can be used for integrity checks or future deduplication logic.

---

## Internal Mechanics

* Uses `uuid.uuid4()` to generate document IDs.
* Truncates generated UUID values to 12 hexadecimal characters.
* Stores uploaded files under `data_store/files/`.
* Stores extracted text and metadata JSON under `data_store/texts/`.
* Maintains an in-memory `_index` dictionary for document lookups.
* Loads `index.json` into memory when the module is imported.
* Writes index updates to disk immediately after files are added or removed.
* Creates the required storage directories automatically when the module is imported.

---

## Helper Functions

| Function        | Description                                     |
| --------------- | ----------------------------------------------- |
| `_new_id()`     | Generates a random 12-character document ID.    |
| `_sha1()`       | Returns the SHA-1 hash of uploaded byte data.   |
| `_save_index()` | Serialises the in-memory index to `index.json`. |
| `_load_index()` | Loads `index.json` into memory when available.  |

---

## Document Lifecycle

1. **Upload** — `save_file()` stores the uploaded file and creates an index record.
2. **Process** — `save_text()` stores extracted text and `save_meta()` stores generated metadata.
3. **Retrieve** — `get_doc()`, `get_text()`, and `get_meta()` provide stored content to the backend pipeline.
4. **List** — `list_docs()` returns basic information for all indexed documents.
5. **Delete** — `delete_doc()` removes the stored file, extracted text, metadata JSON, and index record.

Semantic embeddings are managed separately by the semantic-search service and the FastAPI application layer.

---

## Example Usage

```python id="3qmb2w"
from utils.storage import (
    save_file,
    save_text,
    save_meta,
    get_text,
    get_meta,
    list_docs,
)

with open("example.pdf", "rb") as file:
    record = save_file("example.pdf", file.read())

document_id = record["id"]

save_text(document_id, "Extracted document text.")
save_meta(
    document_id,
    {
        "final": {
            "title": "Example Paper",
            "authors": ["Example Author"],
        }
    },
)

print(record)
print(list_docs())
print(get_text(document_id))
print(get_meta(document_id))
```
