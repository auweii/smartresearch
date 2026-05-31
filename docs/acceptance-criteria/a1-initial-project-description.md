# A1 Acceptance Criteria: Initial Project Description

**Milestone:** Initial Business Case / Project Description  
**Date:** 29 Aug 2025  
**Status:** Baseline scope definition

## Purpose

This file records the original SmartResearch Phase 1 scope baseline. Later assessment files document how this scope evolved during design and implementation.

## Core Functional Acceptance Criteria

| ID | Criterion | Acceptance Measure | Status at A1 |
|---|---|---|---|
| A1-AC-01 | Batch PDF ingestion | The prototype accepts a batch of at least 10 English, text-selectable academic PDFs with validation and error reporting. | `baseline` |
| A1-AC-02 | Structured summaries | Each processed paper returns a summary of no more than 120 words using four fields: objective, method, findings, and limitations. | `baseline` |
| A1-AC-03 | Topic clustering | Uploaded papers are embedded and clustered using an unsupervised method such as K-Means or hierarchical clustering. | `baseline` |
| A1-AC-04 | Cluster labels | Each generated cluster includes automatic keyword or keyphrase labels. | `baseline` |
| A1-AC-05 | Core interface workflow | The React interface supports upload, processing progress, summary browsing, cluster exploration, and search or filtering. | `baseline` |
| A1-AC-06 | Local storage | Uploaded files and generated outputs use lightweight local storage such as filesystem storage and/or SQLite. | `baseline` |
| A1-AC-07 | Structured export | Users can export summaries and cluster labels in CSV and JSON formats. | `baseline` |

## Non-Functional Acceptance Criteria

| ID | Criterion | Acceptance Measure | Status at A1 |
|---|---|---|---|
| A1-NFR-01 | Performance | A 10-paper batch processes in 60 seconds or less, with a target of 5 seconds or less per paper. | `baseline` |
| A1-NFR-02 | Usability | A novice user can locate a known or related paper in 3 clicks or fewer. | `baseline` |
| A1-NFR-03 | Reliability | Malformed or unsupported PDF files do not crash the application and users receive retry guidance. | `baseline` |
| A1-NFR-04 | Privacy | Core processing remains local and does not require third-party transfer of uploaded files. | `baseline` |
| A1-NFR-05 | Maintainability | Dependencies are pinned, API boundaries are documented, and an install check is maintained. | `baseline` |

## Minimum Viable Product

The original MVP is accepted when a user can upload at least 10 PDFs, receive structured summaries and topic clusters, browse papers by cluster, locate a paper within 3 clicks, and export summaries and cluster labels to CSV or JSON.

## Out of Scope at A1

The following items were deliberately excluded from the Phase 1 baseline:

- non-English PDFs
- scanned or image-only PDFs
- OCR
- external database integration
- web crawling
- mobile or native applications
- fine-grained citation or claim extraction
- advanced access control
- multi-tenant accounts
