# SmartResearch — Technical Diagrams

This directory contains the technical diagrams used in the SmartResearch final technical report and supporting documentation.

The diagrams document the completed local-prototype architecture, core processing workflow, frontend routes, API communication patterns, persistent storage model, and generated PDF-export flow.

The directory preserves standalone PNG copies of the final diagram set for repository reference and handover. Additional diagrams and earlier iterations may also appear within the submitted technical-report PDF.

---

## Appendix C: Core Technical Diagrams

| No. | File                                             | Purpose                                                                                                                                                                  |
| --: | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
|  01 | `01-final-system-overview.png`                   | Shows the major frontend, backend, processing-service, local-storage, optional external-service, and PDF-export components.                                              |
|  02 | `02-end-to-end-workflow.png`                     | Shows the user journey from PDF upload through paper review, search, clustering, and PDF export.                                                                         |
|  03 | `03-three-layer-architecture.png`                | Shows the frontend layer, backend and processing layer, and local-storage layer.                                                                                         |
|  04 | `04-runtime-architecture.png`                    | Shows the browser, Vite frontend, FastAPI backend, local filesystem, semantic model, optional external services, and generated output.                                   |
|  05 | `05-document-processing-pipeline.png`            | Shows PDF upload, direct text extraction, OCR fallback, metadata extraction, summary generation, local persistence, semantic indexing, and the returned upload response. |
|  06 | `06-data-storage-model.png`                      | Shows the persistent local-storage structure for uploaded PDFs, extracted text, metadata JSON files, `index.json`, and semantic embeddings.                              |
|  07 | `07-upload-sequence.png`                         | Shows the upload-request flow from frontend file selection through backend processing and the returned completion state.                                                 |
|  08 | `08-search-sequence.png`                         | Shows the keyword, semantic, and hybrid search branches and the returned ranked results.                                                                                 |
|  09 | `09-clustering-sequence.png`                     | Shows semantic-vector loading, document-vector aggregation, adaptive KMeans clustering, TF-IDF keyword labelling, and frontend display.                                  |
|  10 | `10-export-sequence.png`                         | Shows export-option selection, the `/api/export` request, report generation, the returned file response, and the browser download.                                       |
|  11 | `11-route-structure.png`                         | Shows the frontend route structure for `/upload`, `/papers`, `/cluster`, and `/export`.                                                                                  |
|  12 | `12-data-lifecycle.png`                          | Shows the document lifecycle from PDF upload and local persistence through review, search, clustering, export, and deletion.                                             |
|  13 | `13-frontend-backend-communication-sequence.png` | Shows the general React-to-FastAPI request and response flow used across the application.                                                                                |

---

## Diagram Groups

### System Architecture

* `01-final-system-overview.png`
* `03-three-layer-architecture.png`
* `04-runtime-architecture.png`

### Processing and Data Flow

* `02-end-to-end-workflow.png`
* `05-document-processing-pipeline.png`
* `06-data-storage-model.png`
* `12-data-lifecycle.png`

### Sequence Diagrams

* `07-upload-sequence.png`
* `08-search-sequence.png`
* `09-clustering-sequence.png`
* `10-export-sequence.png`
* `13-frontend-backend-communication-sequence.png`

### Frontend Structure

* `11-route-structure.png`

---

## Implementation Notes

* Direct PDF text extraction is attempted before OCR fallback.
* OCR fallback is used for scanned or low-text PDFs when Tesseract OCR is available locally.
* Metadata extraction and CrossRef enrichment are handled by backend processing services.
* Keyword search uses TF-IDF scoring.
* Semantic search and related-paper retrieval use transformer-based embeddings.
* Hybrid search combines keyword and semantic scores.
* Clustering uses document-level semantic representations with TF-IDF keyword labels.
* Uploaded documents, extracted text, metadata, document-index records, and semantic embeddings are stored locally.
* PDF reports are generated as export output and are not stored permanently under `data_store/`.

---

## Diagram Preparation Note

Some of the larger technical diagrams were prepared with AI-assisted tooling during the final documentation period. These diagrams were manually reviewed and amended against the implemented SmartResearch codebase, backend routes, storage structure, and final technical report before submission.

The diagrams were included in the final submitted documentation package and are preserved in this directory as standalone PNG files for repository traceability and handover.

The diagram archive was restored and organised after submission because a late pre-submission repository update overwrote documentation and repository-organisation work completed during the final week. The submitted contribution table and Moodle submission notes provide the corresponding repository-evidence snapshot and workload record.

---

## Reference Notes

* These diagrams support the architecture, implementation, API-design, storage, and workflow sections of the final technical report.
* The diagrams describe the completed SmartResearch local prototype rather than a production-hosted deployment.
* Optional external services are shown separately from the local core workflow.
* The diagrams are retained as standalone PNG files so they can be reviewed outside the technical-report PDF.
