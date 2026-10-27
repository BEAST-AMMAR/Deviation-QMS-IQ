# Project Definition / Project Charter (PD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
The PD/charter is the project-management contract: what's being built, who owns it, what
"done" means, and by when — kept separate from the BRD (why) and PRD (what it does for
the user) so scope/timeline changes don't require rewriting business justification.

### 2. Project summary
| Field | Value |
|---|---|
| Project name | AI-Powered Deviation Intake Module |
| Sponsor / assessor | AIVOA.AI |
| Owner / builder | Muhammad Ammar |
| Context | AI Product Developer Intern practical assessment |
| Deadline | 36 hours from assessment email receipt |
| Primary deliverables | Working application + 2 demo videos + submission form |

### 3. Objectives (see `01_BRD` for full justification)
Build a working, demoable Deviation Management workflow: document/text → AI extraction →
Log Deviation form → AI impact/severity assistance → human review → save — using the
mandated stack (React+Redux, FastAPI, LangGraph+Groq, Postgres).

### 4. Deliverables
1. Working full-stack application (frontend + backend + DB + AI pipeline)
2. Demo video 1 (5–10 min): end-to-end workflow demonstration
3. Demo video 2: code walkthrough (frontend → API → backend → LangGraph → form population)
4. Submission via the provided Google Form
5. This documentation package (not required by the assessment, but reinforces the
   "sensible product decisions" evaluation criterion)

### 5. Roles (worn by one person, but defined distinctly — see `16_QAP` §2 for why this
matters even solo)
| Role | Responsibility |
|---|---|
| Product/Business Analyst | Owns BRD, PRD, user stories |
| Solution Architect | Owns SAD, TRD, database schema |
| AI/ML Engineer | Owns LangGraph graph, prompt design, eval harness |
| Backend Engineer | Owns FastAPI, DB layer, API contracts |
| Frontend Engineer | Owns React/Redux, UI states |
| QA / Delivery Lead | Owns test plan, QAP, risk log, final demo recording |

### 6. Acceptance criteria
The project is "done" when every item in `01_BRD` §6 (Success criteria) is demonstrably
true and both demo videos have been recorded per the assessment's exact requested content.

### 7. Constraints
- Must use the mandated tech stack (non-negotiable per assessment).
- Must not upload code, video, or assignment materials to GitHub or any public repository.
- Must build the Deviation workflow, not the Complaints workflow shown in the reference
  video.

### 8. Out-of-scope reaffirmation
See `01_BRD` §4. Restated here because scope creep under a compressed timeline is the
single most common cause of an incomplete submission — see `13_Risk_Management_Log.md`,
risk R-06.
