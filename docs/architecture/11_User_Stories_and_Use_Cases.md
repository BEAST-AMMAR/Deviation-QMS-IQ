# User Stories & Use Cases
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
User stories give the "why it matters to the user" in one line each; use cases below give
the exact step-by-step flow QA can execute. Both trace back to FRD IDs so nothing here is
untestable.

### 2. User stories
| ID | Story | Acceptance criteria | FR refs |
|---|---|---|---|
| US-01 | As a Quality Officer, I want to paste a raw incident email so that I don't retype it into the form | Form fields populate without manual typing | FR-01, FR-03, FR-06 |
| US-02 | As a Quality Officer, I want to upload a PDF report so that I can log deviations from scanned documents | PDF content extracts into the same fields as pasted text | FR-02, FR-19 |
| US-03 | As a Quality Officer, I want to see how confident the AI is per field so that I know what to double-check | Low-confidence fields are visually distinct | FR-04, FR-05 |
| US-04 | As a Quality Officer, I want to correct a wrong value by just saying so in chat so that I don't have to hunt for the field | Only mentioned fields update; system confirms which ones | FR-11, FR-12 |
| US-05 | As a Quality Officer, I want the AI's severity suggestion to require my confirmation so that nothing is logged without my judgment | Save is blocked until confirmation | FR-08, FR-09, FR-10 |
| US-06 | As a Quality Officer, I want to see a history of what changed and who/what changed it so that the record is defensible in an audit | Audit trail visible per deviation | FR-16 |
| US-07 | As an assessor reviewing this submission, I want to see the AI never fabricate data so that I trust the product judgment behind it | Empty/ambiguous input never produces confidently-wrong fields | FR-07, FR-18 |

### 3. Use cases (detailed flow)

**UC-01 — Extract from pasted text**
*Actor:* Quality Officer. *Precondition:* a draft exists (or is created on first message).
1. User pastes free text into the chat input and sends it.
2. System routes to the extractor node.
3. System returns structured fields with confidence/provenance.
4. Form fields populate with AI-origin highlighting.
*Postcondition:* draft status becomes `Pending Triage` with fields populated.
*Alternate flow:* input contains no recognizable deviation content → system returns a
clarifying chat message and leaves fields empty (no fabrication, FR-07).

**UC-02 — Extract from uploaded document**
Same as UC-01, except input is a PDF/DOCX/TXT file parsed via `pdfplumber` before being
handed to the same extractor prompt (see `07_SAD` §4, PDF-parsing decision).

**UC-03 — Correct a field via chat**
1. User has an existing populated draft.
2. User sends a message describing a correction ("the batch number is actually X").
3. System routes to `patch_node`, diffs only the mentioned field(s).
4. System responds naming exactly which field(s) it updated.
*Postcondition:* only the referenced fields change; all others remain untouched.

**UC-04 — Review and confirm AI risk assessment**
1. Required fields are present in the draft.
2. `risk_assessor` node produces a suggestion; graph hits `interrupt()`.
3. UI shows the confirmation card (see `10_UIUX` §5).
4. User either confirms as-is or edits the severity/action before confirming.
5. Backend resumes the graph with `Command(resume=...)`.
*Postcondition:* draft status becomes `Ready to Commit`.

**UC-05 — Commit the deviation**
*Precondition:* UC-04 completed. User clicks Save Deviation.
1. Backend `committer` node writes the final record to `deviations` (status → committed)
   and appends the confirming event to `deviation_events`.
*Postcondition:* record is read-only; visible via `/deviations/{id}`.

**UC-06 — View audit trail**
User opens the Audit Trail drawer on any deviation → system lists all `deviation_events`
rows in chronological order with actor, field, old/new value.

**UC-07 — Reset draft**
User clicks Reset Form → draft fields clear, chat thread for that draft is cleared client-
side; no `deviations` row is created (drafts are only persisted meaningfully once fields
exist, per `08_TDD` §5's `/drafts/{id}/reset` endpoint).
