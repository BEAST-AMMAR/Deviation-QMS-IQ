# Software Requirements Specification (SRS)
### IEEE 830–style structure
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
This is the single authoritative, formal specification — it consolidates the BRD/PRD/FRD
into one contract and adds the piece none of them cover: **non-functional requirements**
(performance, reliability, security, usability). If any other document conflicts with this
one, this document wins.

### 2. Scope
As defined in `01_BRD` §4. Product name: AI-Powered Deviation Intake Module. Delivered as
a full-stack web application (React/Redux frontend, FastAPI backend, LangGraph/Groq AI
layer, PostgreSQL database).

### 3. Definitions
| Term | Meaning |
|---|---|
| Deviation | An unplanned departure from an approved GMP process/spec/procedure |
| Draft | An in-progress, uncommitted deviation record, mutable via AI or human edits |
| Committed record | A finalized deviation record, read-only after save |
| Extraction | The AI act of turning unstructured text into structured field values |
| Confirmation gate | The mandatory human checkpoint before a severity/impact suggestion is persisted |

### 4. Overall description
**Product perspective:** standalone module, not integrated with a larger QMS suite in this
build (see `01_BRD` §4 out-of-scope). **User characteristics:** non-technical Quality
Officer persona (see `03_PRD` §3). **Assumptions:** internet connectivity for Groq API
calls is available at all times during use; single-user session model.

### 5. Functional requirements
All functional requirements are defined in `04_FRD_Functional_Requirements.md` (FR-01
through FR-19) and are incorporated here by reference to avoid duplication/drift between
documents.

### 6. Non-functional requirements
| ID | Category | Requirement | Reasoning |
|---|---|---|---|
| NFR-01 | Performance | Extraction turnaround should complete within a few seconds under normal conditions | Groq's inference hardware is specifically fast; a slow extraction defeats the product's value proposition |
| NFR-02 | Reliability | Draft state must survive a page refresh mid-correction | Enabled by LangGraph's `PostgresSaver` checkpointer, not in-memory state |
| NFR-03 | Accuracy/Safety | The system must never silently invent a field value not present in source text | Directly required for regulatory trust — see `14_Security_Plan` §3 (prompt-injection/hallucination) |
| NFR-04 | Auditability | Every field mutation must be attributable (who/what) and timestamped | ALCOA+ requirement, see `01_BRD` §2 |
| NFR-05 | Usability | A correction must be achievable without the user knowing internal field names | See `03_PRD` §6 |
| NFR-06 | Portability | The full stack must run via a single `docker compose up` | Removes environment drift between build and demo machines |
| NFR-07 | Maintainability | AI prompt/schema changes must not require frontend code changes | Enforced by contract-first schema design, see `08_TDD` §1 |
| NFR-08 | Security | No secrets (Groq API key, DB credentials) committed to source control | Baseline hygiene, see `14_Security_Plan` §2 |

### 7. External interface requirements
- **Groq API** (LLM inference) — outbound HTTPS, API key via environment variable.
- **PostgreSQL** — internal network only, not exposed publicly in the demo environment.
- **Browser** — modern evergreen browsers (Chrome/Edge/Firefox current versions); no IE11
  support needed.

### 8. Appendix
See `09_Database_Schema_and_ER.md` for the full data contract and `08_TDD` for API
endpoint signatures — both are normative extensions of this SRS, not separate specs that
could disagree with it.
