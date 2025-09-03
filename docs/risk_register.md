# Risk Register — Live Document

This document is the **ongoing risk register** for the SmartResearch project.  
It begins with the snapshot identified during Assignment 1 and will be updated as new risks emerge or existing ones change in status.

---

## Risk Table

| Risk ID | Description | Category       | Likelihood | Impact | Mitigation Strategy                                                                       | Owner   |
|---------|-------------|----------------|------------|--------|------------------------------------------------------------------------------------------|---------|
| R1      | Summary fidelity issues (AI generates inaccurate or misleading digests). | Technical      | Medium     | High   | Pilot evaluation with sample papers; implement rubric-based review.                      | **TBD** |
| R2      | Cluster coherence not interpretable for users. | Technical      | Medium     | Medium | Adjust algorithms; introduce manual tagging fallback.                                    | **TBD** |
| R3      | Schedule slippage due to uneven workload or delays in feature implementation. | Project Mgmt  | Medium     | High   | Weekly check-ins, milestone gates, task allocation tracked via GitHub Issues.            | **Chelsea** |
| R4      | Data licensing breach from non-OA sources. | Compliance     | Low        | High   | Restrict to open-access or UOW-licensed papers only; log licences in metadata.csv.       | **TBD** |
| R5      | Team communication breakdown (async vs scheduled). | Organisational | Medium     | Medium | Discord for daily async comms; Zoom milestone check-ins.                                 | **TBD** |
| R6      | PDF parsing failures. | Technical      | Medium     | Medium | Use robust parser; pre-flight validation; fail gracefully with error messaging.          | **TBD** |
| R7      | Performance bottlenecks on limited hardware. | Technical      | Medium     | Medium | Batch jobs; caching; use distilled models where possible.                                | **TBD** |
| R8      | UI usability is poor / confusing. | Usability      | Medium     | Medium | Quick UX tests; simplify flows; add tooltips and guidance text.                          | **TBD** |
| R9      | Acceptance mismatch with advisor (MVP not aligned). | Stakeholder    | Medium     | High   | Fortnightly demos; maintain written acceptance criteria.                                 | **Chelsea** |
| R10     | Toolchain/library conflicts (breaking changes). | Technical      | Medium     | Medium | Pin versions; lockfile; CI install check.                                                | **TBD** |
| R11     | Evaluation ambiguity (no clear “good” baseline). | Evaluation     | Medium     | Medium | Define rubric; small labelled sample for validation; multiple raters.                    | **TBD** |
| R12     | Stakeholder availability (advisor/team absence). | Organisational | Low        | Medium | Asynchronous Discord workflow; early agendas + shared docs.                             | **Chelsea** |
| R13     | Non-attendance of team members at scheduled meetings, without prior notice. | Organisational | Medium     | High   | Expectations set in Discord (3 Sept); escalated to advisor; logged in minutes and register. | **Chelsea** |

---

## Change Log
- **21 Aug 2025** — Initialised baseline risks R1–R5 *(Chelsea)*.  
- **22 Aug 2025** — Expanded register to full R1–R12; assigned current owners where applicable, left others as **TBD**.  
- **03 Sept 2025** — Logged repeated non-attendance issue as new risk R13 *(Chelsea)*. Advisor notified; agreed it should be kept in record and included in assignments.  
