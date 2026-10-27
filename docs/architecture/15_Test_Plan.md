# Test Plan
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
What gets tested, how, and with what data — including the AI-specific evaluation harness,
which is a different discipline from conventional unit/integration testing and is treated
as its own section rather than an afterthought.

### 2. Test levels

**Unit tests (backend)**
- Pydantic schema validation (`DeviationExtraction`, `RiskAssessment`) accepts valid data
  and rejects malformed data.
- `patch_node` diff logic: given a current state and a correction message, only the
  mentioned fields appear in the output diff.
- Router classification logic on a labeled set of sample messages (extraction vs.
  correction vs. chit-chat).

**Integration tests (backend)**
- Full API round trip against a test database: create draft → send message → assert
  fields populated → confirm → assert committed and read-only.
- `/drafts/{id}/confirm` correctly resumes a paused LangGraph thread (tests R-04 from the
  risk log directly).
- Upload endpoint with a sample PDF returns the same field shape as the text-message path.

**End-to-end tests (frontend)**
- Full UC-01 through UC-07 flows via a browser automation tool (Playwright recommended),
  matching the acceptance criteria in `11_User_Stories_and_Use_Cases.md`.
- Visual state check: AI-origin highlight appears and clears correctly on correction.

### 3. AI evaluation harness (the part generic test plans miss)
Build a small, hand-labeled synthetic dataset — not fetched from any real deviation
records — covering:
1. A clean, well-structured formal incident email.
2. A terse shift-log note ("temp spiked, batch ABC, checked at 2am").
3. A PDF-formatted report (tests the upload path).
4. A deliberately ambiguous report missing a required field (tests FR-07 — must return
   null, not a guess).
5. A report containing an embedded prompt-injection attempt (tests `14_Security_Plan` §3).
6. A correction-only message with no prior draft context (tests graceful handling).

For each, define expected field values by hand, run the extractor, and compare field-by-
field. This is run *before* frontend work begins (`12_Roadmap` Phase 2) so that extraction
bugs are caught cheaply, and it doubles as concrete evidence for the code-walkthrough
video — a genuine differentiator, per the earlier architecture debate.

### 4. Regression checklist (run immediately before recording demo videos)
- [ ] Fresh `docker compose up` from a clean checkout succeeds
- [ ] Paste-text extraction works end-to-end
- [ ] PDF upload extraction works end-to-end
- [ ] Correction message updates only the referenced field(s)
- [ ] Confirmation card blocks Save until acted on
- [ ] Committed record is genuinely read-only (attempt to edit fails at API level, not
      just hidden in UI)
- [ ] Audit trail shows both AI and human-authored events correctly attributed
- [ ] No console errors, no unhandled promise rejections during the full flow

### 5. Out of scope for testing
Load/performance testing and multi-user concurrency testing — not relevant given the
single-user demo scope defined in `01_BRD` §4.
