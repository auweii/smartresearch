# A4 Acceptance Criteria: Design Progress and Initial Implementation

**Milestone:** Progress Report and Initial Design  
**Date:** 27 Mar 2026  
**Status:** Implementation progress checkpoint

## Purpose

This file records the working implementation state at the design-progress milestone. It preserves the original scope while documenting the areas that were implemented, extended, or still required refinement.

## Functional Criteria Snapshot

| ID | Criterion | Design Response | Status at A4 |
|---|---|---|---|
| A4-FR-01 | Upload at least 10 English, text-selectable PDFs | Upload workflow with validation, queueing, and backend ingestion pipeline. | `implemented / refinement required` |
| A4-FR-02 | Generate structured summaries under 120 words using objective, method, findings, and limitations | Summary model and storage designed around consistent sections. | `partially implemented` |
| A4-FR-03 | Cluster papers using unsupervised methods with automatic keyword or keyphrase labels | Backend clustering workflow with topic groupings and a cluster exploration view. | `implemented / refinement required` |
| A4-FR-04 | Provide upload, browse, cluster, and export views | React routing and dedicated page structure map one screen to each major workflow stage. | `implemented` |
| A4-FR-05 | Support search and filtering during paper review | The All Papers view exposes searchable metadata and summary access. | `implemented / refinement required` |
| A4-FR-06 | Export structured results for reuse outside the system | Export view and backend export logic support downstream review workflows. | `implemented / refinement required` |

## Added Prototype Capabilities

| ID | Capability | Rationale | Status at A4 |
|---|---|---|---|
| A4-EXT-01 | OCR fallback | Extends the original text-selectable PDF scope by attempting extraction from scanned or low-text files. | `implemented at prototype level` |
| A4-EXT-02 | Richer metadata handling | Improves title, author, and related metadata retrieval for review. | `implemented at prototype level` |
| A4-EXT-03 | Selectable search modes | Extends basic search into keyword, semantic, and hybrid retrieval modes. | `implemented / refinement required` |
| A4-EXT-04 | Paper detail views | Allows users to inspect paper-level metadata and summary information without leaving the review workflow. | `implemented / refinement required` |
| A4-EXT-05 | Delete controls | Allows users to remove stored papers and related local data where supported. | `implemented at prototype level` |
| A4-EXT-06 | PDF export direction | Adds PDF report generation as the emerging primary export pathway. | `implemented / refinement required` |

## Non-Functional Criteria Snapshot

| ID | Criterion | Design Response | Status at A4 |
|---|---|---|---|
| A4-NFR-01 | Process a 10-paper batch in 60 seconds or less where feasible | Lightweight local architecture and bounded processing pipeline. | `pending benchmark validation` |
| A4-NFR-02 | Keep any paper reachable in 3 clicks or fewer | Four-view workflow and shallow navigation. | `partially met` |
| A4-NFR-03 | Handle malformed files without crashing | Validation, visible errors, and bounded PDF assumptions. | `implemented / refinement required` |
| A4-NFR-04 | Preserve privacy through local-only processing | Local storage and local core processing. | `partially met` |
| A4-NFR-05 | Maintain understandable code and documentation | Frontend/backend separation, modular services, and repository documentation. | `implemented at documentation level` |

## Scope Change Notes

The original privacy statement was narrowed because optional external metadata enrichment introduces a limited external dependency. OCR moved from out-of-scope to an implemented prototype extension. PDF export emerged as the likely supported final pathway, while CSV and JSON still required validation.
