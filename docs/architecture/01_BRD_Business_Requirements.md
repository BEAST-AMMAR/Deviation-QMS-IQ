# Business Requirements Document (BRD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
A BRD exists to force one question before any code is written: *what business problem
justifies this build, and how will we know it's solved?* Skipping this step is the single
biggest reason technically-good AI prototypes get rejected in review — they solve an
interesting problem instead of the stated one. This document is the traceability anchor:
every requirement in the PRD/FRD/SRS should point back to a line here.

### 2. Background
AIVOA.AI builds AI-native Quality Management System (QMS) software for pharmaceutical
manufacturers. In regulated drug manufacturing, a **deviation** is any unplanned departure
from an approved process, specification, or procedure (e.g., a batch parameter drifting
outside its approved range). Every deviation must be logged, assessed for impact and
severity, and tracked — this is a regulatory requirement (GMP), not a business preference.

Today this logging step is manual: a quality officer reads an incident report (email,
handwritten note, lab result) and re-types it into a structured form, field by field. This
is slow, inconsistent between officers, and error-prone under time pressure — a well-known,
long-standing pain point in QMS software generally (not a claim specific to any measured
dataset in this assessment).

### 3. Business objectives
| ID | Objective | Rationale |
|---|---|---|
| BO-1 | Reduce manual transcription effort in deviation logging | The AI should do the typing; the human should do the judgment |
| BO-2 | Keep humans authoritative over compliance-critical decisions | Severity/impact classification carries regulatory weight — AI assists, never decides alone |
| BO-3 | Make every AI action traceable and reversible | Regulated records must be attributable and auditable (ALCOA+) |
| BO-4 | Demonstrate product judgment, not just API integration | This is an evaluation criterion stated directly in the assessment brief |

### 4. Scope
**In scope:** a single-module workflow — Deviation intake, AI-assisted extraction from
pasted text or an uploaded document, AI-suggested impact/severity with human confirmation,
correction via natural-language follow-up, and committing the record.

**Out of scope (explicitly):** the Customer Complaints module (shown only as a UI/interaction
reference, not to be built), multi-tenant/multi-site administration, full 21 CFR Part 11
electronic-signature compliance, user account management/SSO, CAPA (Corrective and
Preventive Action) workflows, reporting/analytics dashboards, and production-grade
horizontal scaling. These are named out-of-scope rather than left silently unaddressed,
so a reviewer knows they were considered and deliberately deferred, not missed.

### 5. Stakeholders
| Stakeholder | Interest |
|---|---|
| AIVOA.AI (assessor) | Evaluating product sense, AI engineering, and full-stack execution |
| Quality Officer (end user persona) | Wants deviations logged fast, accurately, without re-typing |
| Developer (you) | Needs a working, explainable, demoable system built under time pressure |

### 6. Success criteria
These are functional/behavioral, not fabricated adoption or ROI numbers:
- A pasted incident report or uploaded PDF results in a populated form with zero manual
  field typing.
- Every AI-suggested value is visibly marked as AI-origin until a human confirms it.
- A natural-language correction updates only the fields mentioned, and the system states
  which fields changed.
- No deviation record can be committed without an explicit human confirmation step on the
  severity/impact assessment.
- Every field change (AI or human) is visible in an audit trail with who/what made it and
  when.

### 7. Assumptions & constraints
- Single-user demo context; no multi-user concurrency guarantees required.
- Groq API availability and rate limits are external dependencies outside this project's
  control (mitigation in `13_Risk_Management_Log.md`).
- No real patient or personal data is used — all sample deviations are synthetic.
