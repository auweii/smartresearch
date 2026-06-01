# SmartResearch — Risk Register

This document records the SmartResearch project risk register across the full project lifecycle.

It began as an Assignment 1 planning document and was updated through final submission to record technical, organisational, compliance, evaluation, handover, and repository-management risks. The register distinguishes risks that were mitigated during the prototype, risks that occurred during delivery, and risks that remain relevant for future development.

---

## Status Definitions

| Status                  | Meaning                                                                                                         |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| `closed`                | Risk was addressed sufficiently for the submitted local prototype.                                              |
| `mitigated`             | Risk remains possible, but controls reduced its impact during the project.                                      |
| `occurred / controlled` | Risk materialised during the project and was managed through documented corrective action.                      |
| `open / future work`    | Risk remains relevant if the project is extended beyond the submitted prototype.                                |
| `deferred`              | Risk relates primarily to production deployment or unsupported functionality outside the final prototype scope. |

---

## Final Risk Register

| Risk ID | Description                                                                                                                              | Category                               | Likelihood | Impact | Mitigation and Closeout                                                                                                                                                                                                                                                                                                  | Owner             | Final Status            |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | ----------------------- |
| **R1**  | AI-assisted summaries may be inaccurate, incomplete, misleading, or inconsistently structured.                                           | Technical / Quality                    | Medium     | High   | Extractive summaries were implemented with fallback handling. The final documentation states that strict objective, method, findings, and limitations formatting is not fully enforced and that summary quality requires user review. Add structured-output validation and word-count enforcement in future development. | Future Maintainer | `open / future work`    |
| **R2**  | Generated clusters may not be sufficiently coherent or interpretable for users.                                                          | Technical / Evaluation                 | Medium     | Medium | KMeans clustering and TF-IDF keyword labelling were implemented at prototype level. Cluster-label quality and formal evaluation remain refinement areas. Future work should improve keyphrase extraction, allow label refinement, and introduce benchmark datasets.                                                      | Future Maintainer | `open / future work`    |
| **R3**  | Schedule slippage may compress implementation, testing, documentation, and final quality assurance.                                      | Project Management                     | High       | High   | This risk occurred during the final submission period. Scope controls, final prioritisation, manual verification, contribution records, and documentation triage were used to preserve the core workflow and submission package.                                                                                         | Chelsea           | `occurred / controlled` |
| **R4**  | Uploaded papers may introduce licensing, copyright, or data-handling concerns.                                                           | Compliance                             | Low        | High   | The final prototype is intended for local use with papers that users are permitted to access and process. The application does not provide licensed-content distribution. Future deployment should include explicit usage guidance, retention controls, and privacy notices.                                             | Future Maintainer | `mitigated`             |
| **R5**  | Team communication breakdown may delay decisions, implementation, and submission work.                                                   | Organisational                         | High       | High   | Discord, Zoom, asynchronous updates, meeting minutes, and advisor escalation were used throughout the project. Communication gaps still contributed to compressed final work and uneven workload distribution.                                                                                                           | Chelsea / Team    | `occurred / controlled` |
| **R6**  | PDF parsing may fail for malformed, encrypted, scanned, or unusual documents.                                                            | Technical                              | Medium     | Medium | Direct PDF extraction and OCR fallback were implemented. Broader malformed-PDF robustness remains limited and requires stronger validation, clearer error handling, and wider edge-case testing.                                                                                                                         | Future Maintainer | `open / future work`    |
| **R7**  | Processing may become slow on limited hardware, especially for larger batches, OCR, semantic embeddings, or AI-assisted summaries.       | Performance                            | Medium     | Medium | Lightweight local storage, cached TF-IDF data, chunked semantic embeddings, and optional GPU support reduce some performance pressure. The original 10-paper benchmark was not fully validated across machines and datasets.                                                                                             | Future Maintainer | `open / future work`    |
| **R8**  | The interface may become confusing as more features are added.                                                                           | Usability                              | Medium     | Medium | The final interface retains a shallow four-stage workflow: Upload, All Papers, Cluster, and Export. Screenshots and the user manual document the intended navigation. Formal user testing remains limited.                                                                                                               | Future Maintainer | `mitigated`             |
| **R9**  | The implemented product may diverge from advisor expectations or the original requirements.                                              | Stakeholder / Scope                    | Medium     | High   | Acceptance-criteria snapshots, requirements traceability, advisor discussions, scope-change documentation, and explicit deferred-feature records were maintained across the project.                                                                                                                                     | Chelsea           | `mitigated`             |
| **R10** | Python, frontend, OCR, semantic-model, or library dependencies may create installation conflicts.                                        | Technical / Toolchain                  | Medium     | Medium | Dependency files were maintained for standard and optional NVIDIA GPU installations. Tesseract OCR is documented as a separate local prerequisite. Future work should add automated installation checks and environment validation.                                                                                      | Future Maintainer | `mitigated`             |
| **R11** | Summary quality, cluster usefulness, and retrieval relevance may be difficult to evaluate without a clear benchmark.                     | Evaluation                             | Medium     | Medium | Manual testing and limitation framing were used for the prototype. Formal evaluation remains deferred. Future development should use labelled datasets, scoring rubrics, and multiple evaluators.                                                                                                                        | Future Maintainer | `open / future work`    |
| **R12** | Advisor or stakeholder availability may delay feedback and sign-off.                                                                     | Organisational                         | Medium     | Medium | Asynchronous communication, early agendas, rescheduling, written records, and alternative recorded walkthroughs were used when meetings could not proceed as planned.                                                                                                                                                    | Chelsea           | `occurred / controlled` |
| **R13** | Team members may miss scheduled meetings without prior notice.                                                                           | Organisational                         | Medium     | High   | Attendance issues were logged in meeting minutes, raised with the advisor, and retained in the project record. Asynchronous records reduced the risk of undocumented decisions.                                                                                                                                          | Chelsea           | `occurred / controlled` |
| **R14** | Uneven workload distribution may place excessive delivery pressure on a reduced number of active contributors.                           | Organisational / Project Management    | High       | High   | This risk occurred. The contribution table records verified completed work, reported but unverified work, repository evidence, and final workload distribution. Scope control and submission-critical prioritisation were used to complete the project.                                                                  | Chelsea / Team    | `occurred / controlled` |
| **R15** | Scope creep may reduce completion quality by introducing too many features for a local capstone prototype.                               | Scope                                  | High       | High   | Production features were explicitly deferred. The final report distinguishes implemented, prototype-level, partial, and deferred functionality rather than claiming unsupported features.                                                                                                                                | Chelsea           | `mitigated`             |
| **R16** | Frontend and backend export options may become misaligned.                                                                               | Technical / Scope                      | Medium     | High   | PDF report export was retained as the supported final pathway. CSV and JSON export remained deferred unless independently implemented and tested. Unsupported formats should be removed or disabled in any future interface revision.                                                                                    | Future Maintainer | `mitigated`             |
| **R17** | CrossRef, Semantic Scholar, or other external-service behaviour may be unavailable, inconsistent, or dependent on metadata quality.      | External Dependency                    | Medium     | Medium | The core workflow remains local. External metadata enrichment and recommendation behaviour are optional and use fallbacks where available. Documentation must avoid presenting external results as guaranteed.                                                                                                           | Future Maintainer | `mitigated`             |
| **R18** | OCR fallback may fail when Tesseract OCR is not installed or configured locally.                                                         | Technical / Environment                | Medium     | Medium | OCR is treated as an environment-dependent extension. The backend documentation states that `pytesseract` requires the separate Tesseract executable to be installed and available on the system path. Direct extraction still works without OCR.                                                                        | Future Maintainer | `mitigated`             |
| **R19** | Limited automated testing may allow regressions across upload, search, clustering, storage, and export workflows.                        | Quality Assurance                      | High       | High   | Manual runtime verification, screenshots, endpoint checks, and evidence records were used for the submitted prototype. Future work should add unit, integration, frontend, and regression tests.                                                                                                                         | Future Maintainer | `open / future work`    |
| **R20** | Late or unverified implementation changes may arrive too close to submission for reliable integration testing and documentation updates. | Project Management / Quality Assurance | High       | High   | This risk occurred during the final submission period. The contribution table froze a timestamped repository-evidence snapshot before the deadline. Reported work that could not be independently reviewed against the repository was recorded separately from verified contributions.                                   | Chelsea           | `occurred / controlled` |
| **R21** | A late repository update may overwrite recent documentation, project records, or repository-organisation work.                           | Repository Management                  | Medium     | High   | This risk occurred immediately before final submission. The submitted source-code archive preserved the evaluation copy. Missing repository documentation was recovered from a local backup and restored after submission. Moodle submission notes document the incident for transparency.                               | Chelsea           | `occurred / controlled` |
| **R22** | Repository documentation may drift out of alignment with the submitted build after late code or documentation changes.                   | Documentation / Handover               | High       | High   | The submitted ZIP remains the official evaluation copy. Post-submission repository work is limited to README restoration, archive notes, documentation structure, and handover clarity. The Moodle submission notes and contribution table record the repository snapshot used for submission evidence.                  | Chelsea           | `occurred / controlled` |
| **R23** | Large documentation artefacts may exceed GitHub browser-upload limits and become inaccessible through the repository alone.              | Documentation / Handover               | Medium     | Medium | The final technical report was submitted through Moodle before the deadline. A Google Drive link is preserved under `docs/a6/technical-report-link.txt` because the PDF is not duplicated in the repository.                                                                                                             | Chelsea           | `mitigated`             |
| **R24** | Local filesystem storage may be insufficient for multi-user, production-scale, or sensitive-data deployment.                             | Security / Architecture                | Medium     | High   | The final product is documented as a local prototype. Production use would require authentication, role-based access control, database-backed persistence, retention controls, deployment hardening, and clearer privacy controls.                                                                                       | Future Maintainer | `deferred`              |
| **R25** | Local stored files, extracted text, metadata, and semantic embeddings may persist after use unless explicitly deleted.                   | Security / Privacy                     | Medium     | Medium | Delete functionality is available at prototype level, and the local-storage model is documented. Future versions should add clearer retention guidance, bulk cleanup tools, and user-facing storage notices.                                                                                                             | Future Maintainer | `open / future work`    |

---

## Key Risk Closeout Summary

The final SmartResearch prototype successfully demonstrates the connected local workflow for PDF upload, extraction, metadata handling, summarisation, browsing, keyword search, semantic search, hybrid search, clustering, deletion, similarity support, recommendations where available, and PDF report export.

The remaining open risks do not invalidate the submitted capstone prototype. They define the work required before any production deployment or larger-scale use.

The highest-impact delivery risks were organisational and repository-related rather than purely technical. Uneven contribution, compressed final integration, late unverified inputs, repository-state overwrite, and documentation drift all materialised during the final submission period. These were controlled through scope reduction, timestamped repository evidence, local backups, Moodle disclosure, post-submission documentation restoration, and preservation of the submitted source-code ZIP as the official evaluation copy.

---

## Deferred Production Controls

The following controls remain outside the submitted local-prototype scope:

* Authentication and user accounts
* Role-based permissions
* Database-backed persistence
* Cloud deployment
* Multi-user collaboration
* Enterprise security controls
* Production-scale corpus handling
* Full automated regression testing
* Formal summary-quality evaluation
* Formal cluster-quality evaluation
* Stronger malformed-PDF handling
* Bulk cleanup and retention tooling
* Non-English document support
* Mobile or native applications

---

## Change Log

* **21 Aug 2025** — Initialised baseline risks R1–R5. *(Chelsea)*
* **22 Aug 2025** — Expanded register to R1–R12 and assigned initial owners where applicable. *(Chelsea)*
* **03 Sep 2025** — Added R13 after repeated non-attendance at scheduled meetings. Advisor notified and issue retained in project records. *(Chelsea)*
* **Mar 2026** — Updated technical risks following integrated prototype progress, including OCR fallback, metadata enrichment, semantic search, clustering, summary-display issues, and recorded walkthrough requirements. *(Chelsea)*
* **May 2026** — Added scope-control, export-alignment, environment-dependency, external-service, testing, and uneven-contribution risks based on final implementation and documentation review. *(Chelsea)*
* **31 May 2026, 11:30 PM AEST** — Contribution table and repository-evidence snapshot frozen before the Assignment 6 deadline. *(Chelsea)*
* **1 Jun 2026** — Added final repository-restoration, documentation-drift, and large-artefact handover risks following the late pre-submission repository overwrite and post-submission documentation recovery. *(Chelsea)*

---

## Reference Notes

* Historical assignment folders preserve milestone-specific artefacts and acceptance snapshots.
* The submitted source-code ZIP remains the official Assignment 6 evaluation copy.
* Post-submission repository updates restore documentation and repository organisation without altering the submitted evaluation copy.
* The final technical report, contribution table, Moodle submission notes, acceptance-criteria snapshots, meeting records, and repository history provide the supporting closeout evidence.

