# Functional Requirements Document (FRD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
The PRD explains *why* a feature matters to the user; this document lists *exactly* what
the system must do, in a form a developer can build against and a tester can check off
line by line — no interpretation required.

### 2. Functional requirements

| ID | Requirement | Priority | Related use case |
|---|---|---|---|
| FR-01 | User can paste free text into the AI panel input | Must | UC-01 |
| FR-02 | User can drag-and-drop or browse-upload a PDF/DOCX/TXT file into the AI panel | Must | UC-02 |
| FR-03 | System extracts: site/plant, date of occurrence, title, source, related product/material, batch/lot number, detailed description | Must | UC-01, UC-02 |
| FR-04 | Each extracted field carries a confidence level (high/medium/low) | Should | UC-01 |
| FR-05 | Each extracted field carries a source snippet (the input phrase it was derived from) | Should | UC-01 |
| FR-06 | Extracted fields visually populate the left form with a highlight indicating AI-origin, unconfirmed status | Must | UC-01, UC-02 |
| FR-07 | System never fabricates a value for a field it cannot find in the input — returns null/empty and flags it instead | Must | UC-06 |
| FR-08 | System generates a suggested severity (Minor/Major/Critical), a suggested next action, and a short reasoning string | Must | UC-04 |
| FR-09 | System pauses and requires explicit human confirmation before the severity assessment becomes part of a committed record | Must | UC-04 |
| FR-10 | Human can edit the AI-suggested severity/impact before confirming | Must | UC-04 |
| FR-11 | User can send a follow-up natural-language message correcting one or more fields | Must | UC-03 |
| FR-12 | System updates only the fields referenced in the correction message, and states which fields changed | Must | UC-03 |
| FR-13 | User can manually edit any form field directly as a fallback correction method | Must | UC-03 |
| FR-14 | User can commit ("Save Deviation") only after the confirmation gate (FR-09) has been passed | Must | UC-05 |
| FR-15 | User can reset the draft, discarding unsaved AI/human edits | Should | UC-07 |
| FR-16 | Every field change (AI-authored or human-authored) is recorded in an append-only audit log with actor, old value, new value, timestamp | Must | UC-06 |
| FR-17 | Committed deviations become read-only in the UI (no silent post-commit editing) | Should | UC-05 |
| FR-18 | System handles unrecognized/irrelevant chat input gracefully (does not crash or hallucinate a deviation from empty input) | Must | UC-06 |
| FR-19 | System supports at minimum PDF, DOCX, and TXT for the upload path | Should | UC-02 |

### 3. Field list (Log Deviation form — matches assessment reference UI)
Site/Plant\*, Date of Occurrence\*, Title/Short Description\*, Source\*, Related
Product/Material, Batch/Lot Number, Detailed Description\* (2000-char cap), Initial
Impact\*, Initial Severity\*. (\* = required before commit, per FR-14.)

### 4. Traceability
Every FR above maps to a business objective in `01_BRD` §3 and a use case in
`11_User_Stories_and_Use_Cases.md`. No FR exists without a BO it serves — this is the
traceability check a reviewer would run first.
