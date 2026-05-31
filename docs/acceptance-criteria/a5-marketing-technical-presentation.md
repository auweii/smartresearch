# A5 Acceptance Criteria: Marketing and Technical Presentation

**Milestone:** Marketing and Technical Presentation  
**Date:** 25 May 2026  
**Status:** Public-facing and technical-claim verification checkpoint

## Purpose

This file records the product claims presented during the A5 marketing and technical materials. Each claim must remain aligned with the final merged build. A polished video does not magically turn an unfinished endpoint into a feature.

## User-Facing Product Claims

| ID | Claim | Acceptance Measure | Status at A5 |
|---|---|---|---|
| A5-AC-01 | Centralised paper workflow | Users can upload, organise, summarise, search, cluster, and export research material through one interface. | `pending final verification` |
| A5-AC-02 | Metadata extraction | Uploaded documents expose key metadata such as title, authors, and publication details where available. | `implemented at prototype level` |
| A5-AC-03 | AI-assisted summaries | Processed papers display generated summaries to support early screening. | `implemented / refinement required` |
| A5-AC-04 | Semantic search | Users can search by meaning rather than exact keyword matching alone. | `implemented at prototype level` |
| A5-AC-05 | Clustering | Similar papers are grouped into topic clusters with generated keywords. | `implemented / refinement required` |
| A5-AC-06 | Report export | Users can generate reusable exportable reports from processed research information. | `pending final verification` |

## Technical Claims

| ID | Claim | Acceptance Measure | Status at A5 |
|---|---|---|---|
| A5-TECH-01 | Layered architecture | React/Vite frontend, FastAPI backend, processing services, and local storage are documented as separate responsibilities. | `implemented` |
| A5-TECH-02 | PDF extraction | Standard text-selectable PDFs are processed through direct PDF text extraction. | `implemented` |
| A5-TECH-03 | OCR fallback | Low-text or scanned PDFs trigger Tesseract-based OCR fallback where local setup permits. | `implemented at prototype level` |
| A5-TECH-04 | Semantic retrieval | SPECTER2 embeddings support semantic search and related-paper retrieval. | `implemented at prototype level` |
| A5-TECH-05 | Hybrid retrieval | Keyword matching and semantic similarity are combined for hybrid search. | `implemented at prototype level` |
| A5-TECH-06 | Clustering implementation | K-Means clustering and TF-IDF keyword extraction support topic grouping. | `implemented / refinement required` |
| A5-TECH-07 | Local persistence | PDFs, extracted text, metadata, summaries, and semantic data are stored locally for the prototype workflow. | `implemented at prototype level` |

## Claim Boundaries

The following wording must remain controlled in the final repository and documentation:

- SmartResearch is a local web application prototype, not a hosted public service.
- CSV and JSON export must not be described as final supported formats unless final testing proves they work.
- Summary quality, cluster labels, metadata quality, and relevance scores require user review.
- External recommendations depend on metadata quality, network availability, and third-party services.
- Collaboration, cloud deployment, topic modelling, analytics, and stronger AI models remain future work.
