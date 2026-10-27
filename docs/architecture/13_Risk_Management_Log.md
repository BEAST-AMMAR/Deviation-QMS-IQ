# Risk Management Log
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
A living register of what could go wrong, how likely/severe it is, and the mitigation
already designed into the system (or the action to take if it occurs) — reviewed and
updated as the build progresses, not written once and forgotten.

### 2. Risk register

| ID | Risk | Category | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | LLM hallucinates a field value not present in source text | AI quality | Medium | High | Explicit "return null, never guess" prompting (NFR-03); confidence/provenance fields surface uncertainty; eval harness (`15_Test_Plan` §3) tests specifically for this | Mitigated by design |
| R-02 | Groq model named in the assignment (`gemma2-9b-it`) is deprecated/unavailable | Technical | Confirmed | Medium | Already substituted with `llama-3.3-70b-versatile` in `06_TRD` §3 | Resolved |
| R-03 | Groq API rate limits hit during heavy testing/demo recording | Technical | Low–Medium | Medium | Two-tier model usage reduces call volume on the large model; retry/backoff on 429s | Planned |
| R-04 | LangGraph `interrupt()`/checkpoint state resumes incorrectly (wrong thread, stale state) | Technical | Low | High | Use `draft_id` consistently as `thread_id`; test resume path explicitly in `15_Test_Plan` §2 | Planned |
| R-05 | Prompt injection via uploaded document (e.g., document text instructing the AI to set severity to "Minor" regardless of content) | Security | Medium | High | See `14_Security_Plan.md` §3 — treat all document/pasted content as untrusted data, not instructions; system prompt explicitly scopes the model's role | Mitigated by design |
| R-06 | Scope creep beyond `01_BRD` §4 out-of-scope items delays core deliverables | Project management | Medium | High | Out-of-scope list defined upfront and reaffirmed in `02_PD` §8 | Ongoing discipline |
| R-07 | PDF parsing fails on a malformed/scanned (image-only) PDF | Technical | Medium | Low | Graceful failure message rather than a crash; document format expectations set in `06_TRD`/`04_FRD` FR-19 | Planned |
| R-08 | Committed record accidentally becomes editable, undermining the audit-trail story | Compliance/product | Low | Medium | Read-only enforcement at both API and UI layer (FR-17) | Planned |
| R-09 | Docker Compose environment differs between build and demo-recording machine | Technical | Low | Medium | Single `docker compose up` as NFR-06; test on a clean checkout before recording | Planned |
| R-10 | Two required demo videos don't match the assessment's exact content bullets | Delivery | Low | High | Script videos directly against the assessment's deliverable bullets before recording (`12_Roadmap` Phase 8) | Planned |

### 3. Review cadence
Revisit this log at the end of each roadmap phase (`12_Roadmap.md` §3) — a risk that
materializes mid-build should be added here immediately, not just fixed silently.
