# A6 Acceptance Criteria: Final Product and Documentation

**Milestone:** Final Product and Documentation  
**Date:** 1 Jun 2026  
**Status:** Pre-submission acceptance snapshot

## Purpose

This file records the pre-submission acceptance status of SmartResearch based on the repository state and supporting artefacts available at the time of preparation. It distinguishes implemented core features, prototype-level extensions, partially implemented requirements, deferred items, and work that still requires final verification against the merged repository and test evidence.

## Document Snapshot Note

This document records the implementation status of SmartResearch as of the date of preparation. The acceptance matrix is based on the repository state and supporting artefacts available at that time. Features, code changes, or testing evidence submitted after this snapshot may not be reflected in this record unless they were incorporated before the final documentation package was prepared.

## Functional Acceptance Matrix

| ID | Type | Requirement | Final Implementation Direction | Final Status |
|---|---|---|---|---|
| FR1 | Core | Batch upload English academic PDFs | Upload page and Dropzone allow users to select or drag multiple PDF files into the backend processing workflow. | `implemented`; 10-paper benchmark requires final evidence |
| FR2 | Core | Extract text from uploaded papers | Backend extracts and stores text for browsing, search, summarisation, clustering, and export-related workflows. | `implemented` |
| FR3 | Additional | Handle scanned or low-text PDFs | OCR fallback is attempted when direct extraction produces insufficient text. | `implemented at prototype level` |
| FR4 | Core | Generate paper summaries | Backend generates AI-assisted summary output from available paper content. | `partially implemented`; strict four-field formatting and word-limit enforcement require refinement |
| FR5 | Core | Extract and store metadata | System stores and displays title, author, year, DOI, venue, and related fields where available. | `implemented at prototype level` |
| FR6 | Additional | Improve metadata accuracy and reliability | Metadata scoring, layout-aware extraction, validation, enrichment, and confidence handling are used where available. | `implemented at prototype level` |
| FR7 | Core | Browse uploaded papers | All Papers page displays stored papers in a central table. | `implemented` |
| FR8 | Additional | Inspect detailed paper information | Paper detail views expose metadata, summaries, extracted text, and related information where available. | `implemented at prototype level` |
| FR9 | Core / Additional | Search and filter processed papers | All Papers page supports keyword, semantic, and hybrid search modes. | `implemented and extended` |
| FR10 | Additional | Keyword search | TF-IDF and cosine similarity support exact-term and near-exact retrieval. | `implemented` |
| FR11 | Additional | Semantic search | SPECTER2-based embeddings support meaning-level retrieval. | `implemented at prototype level`; performance depends on model loading and corpus size |
| FR12 | Additional | Hybrid search | Keyword and semantic scores are combined for balanced retrieval. | `implemented at prototype level` |
| FR13 | Core | Cluster papers by topic | K-Means clustering groups document-level semantic representations. | `implemented at prototype level`; final evidence required |
| FR14 | Core | Generate cluster labels | TF-IDF keywords provide cluster descriptions. | `implemented / refinement required` |
| FR15 | Additional | Inspect grouped papers in a cluster | Cluster detail view displays papers assigned to a selected cluster. | `pending final verification` |
| FR16 | Additional | Similar-document retrieval | Related uploaded papers may be returned from the stored corpus. | `implemented at backend prototype level`; user-facing exposure must be confirmed |
| FR17 | Stretch | External recommendations | External related-paper recommendations may be attempted where metadata and network access permit. | `implemented at backend prototype level`; optional dependency noted |
| FR18 | Additional | Delete stored papers | Users can remove stored papers and related local data where supported. | `implemented at prototype level` |
| FR19 | Core / Changed | Generate downloadable report output | PDF report generation is the intended final export pathway. | `pending final verification` |
| FR20 | Core / Deferred | Export CSV and JSON | Original structured export formats remain unconfirmed. | `deferred unless final testing proves support` |

## Non-Functional Acceptance Matrix

| ID | Requirement | Final Status | Notes |
|---|---|---|---|
| NFR1 | Process a 10-paper batch within the original performance target | `not fully validated` | OCR fallback, AI summary generation, and semantic processing can increase processing time. |
| NFR2 | Keep papers reachable within 3 clicks or fewer | `mostly supported` | Upload, All Papers, Cluster, and Export views use shallow navigation. |
| NFR3 | Handle malformed files without crashing | `partially implemented` | Error handling exists, but broader malformed-PDF robustness remains a limitation. |
| NFR4 | Keep core processing and storage local | `mostly implemented` | Optional metadata enrichment and recommendation services may use external requests. |
| NFR5 | Keep the codebase understandable and extendable | `implemented at documentation level` | Source code, setup guidance, limitations, testing records, and future-work notes support handover. |

## Deferred Production Features

The following items remain outside the final local-prototype scope:

- authentication
- user accounts
- role-based permissions
- cloud persistence
- production deployment
- multi-user collaboration
- enterprise security controls
- production-scale corpus handling
- full automated regression testing
- non-English document support
- mobile or native applications
- fine-grained citation and claim extraction

## Final Verification Checklist

Update this section after the final merged repository and screenshots are available.

| Check | Required Evidence | Status |
|---|---|---|
| Multiple PDF upload succeeds | Screenshot or test record | `pending final verification` |
| 10-paper batch benchmark recorded | Timing evidence | `pending final verification` |
| Summary output appears in the interface | Screenshot or test record | `pending final verification` |
| Keyword search returns ranked results | Screenshot or test record | `pending final verification` |
| Semantic search returns meaning-related results | Screenshot or test record | `pending final verification` |
| Hybrid search returns combined results | Screenshot or test record | `pending final verification` |
| Clusters display counts and keyword labels | Screenshot or test record | `pending final verification` |
| Cluster detail view displays grouped papers | Screenshot or test record | `pending final verification` |
| PDF report exports and opens successfully | Downloaded report screenshot or test record | `pending final verification` |
| CSV and JSON support confirmed or marked deferred | Final backend test result | `pending final verification` |
| Malformed-PDF behaviour recorded | Test record | `pending final verification` |

## Final Acceptance Summary

SmartResearch is accepted as a local capstone prototype when the final merged build demonstrates the connected workflow from upload to review, search, clustering, and PDF report generation, with limitations recorded honestly. The original CSV and JSON export commitment must remain deferred unless final testing proves support. Strict summary formatting, batch performance benchmarking, cluster-label quality, malformed-PDF robustness, and production-level deployment remain refinement or future-work items.
