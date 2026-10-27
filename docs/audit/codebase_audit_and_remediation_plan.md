# DeviationIQ: Comprehensive Architectural, Pipeline & Usability Audit

**Audit Date**: September 27, 2026  
**System Scope**: End-to-end audit of Frontend React application, LangGraph workflow, FastAPI routers, Groq model integration, SQLAlchemy/SQLite database state, and 21 CFR Part 11 / GxP compliance lifecycle.

---

## 1. Executive Summary & Root Cause Matrix

The user's reported inability to:
1. **Move to the next file once a file is committed**
2. **Transition to the next operation after clicking "Committed"**
3. **Save the deviation even when all required fields are filled**
4. **Advance in a continuous multi-file / iterative workflow**

stems from **7 interlocking architectural bottlenecks** across the frontend state machine, API routes, and graph execution flow.

| ID | Category | Component | Root Cause | Impact |
|:---|:---|:---|:---|:---|
| **BUG-01** | Workflow Dead-End | `AICopilotPanel.jsx`, `DeviationFormPanel.jsx` | `isCommitted` hides dropzone, hides chat input, disables inputs, and disables `Reset Form`. Zero "New Deviation" CTA exists. | User is permanently frozen on the committed record with no path to process a 2nd file without a hard browser reload. |
| **BUG-02** | Inert UI / Broken Action | `DeviationFormPanel.jsx` (L206) | "Save Deviation" button has **no `onClick` handler** and is hardcoded to `disabled={status !== 'committed'}`. | User can never actively click "Save Deviation". It acts as a passive read-only label rather than a form submission trigger. |
| **BUG-03** | Manual Entry Blockade | `drafts.py`, `ConfirmationCard.jsx` | System only allows `status = 'committed'` via the AI Confirmation Card (`/api/drafts/{id}/confirm`). | If an operator manually fills all 7 fields, the AI interrupt never fires, so the record can never be saved. |
| **BUG-04** | Field Sync Disconnect | `draftSlice.js`, `drafts.py` | Manual edits in `DeviationFormPanel.jsx` update local Redux only; no backend sync endpoint exists. | Backend database & AI reasoning remain blind to human edits. On confirm, manually typed field data is lost. |
| **BUG-05** | Date Exclusion in Commit | `drafts.py` (L437) | `confirm_assessment` iterates through 6 fields but omits `date_of_occurrence` from update list. | `date_of_occurrence` can fail to persist upon final record commitment. |
| **BUG-06** | Fragile JSON Parsing | `nodes.py` (`_parse_json_response`) | Relies strictly on `startswith("```")` and `json.loads`. Fails if Groq outputs conversational preamble or postscript. | Intermittent extraction failures; assistant claims "could not extract any data" when LLM adds polite preamble text. |
| **BUG-07** | Scope Gate Blockade | `builder.py` (`_should_assess_risk`) | Requires both `title` AND `detailed_description`. If `title` is not extracted from raw text, risk assessment never runs. | Form gets stuck in `pending_triage`, Confirmation Card never appears, and form remains uncommittable. |

---

## 2. In-Depth Technical Analysis

### A. The "Locked State Dead-End" (BUG-01)
In `AICopilotPanel.jsx`:
```jsx
// Line 159 & Line 215:
{!isCommitted && <div {...getRootProps()} className="upload-zone">...</div>}
{!isCommitted && <div className="chat-input-area">...</div>}
```
In `DeviationFormPanel.jsx`:
```jsx
// Line 197:
<button className="btn btn-danger btn-sm" onClick={handleReset} disabled={isCommitted}>
```
When `confirmAssessment` completes:
- The dropzone is removed from the DOM.
- The chat input is removed from the DOM.
- The form inputs are locked (correct for 21 CFR Part 11).
- But the Reset button is disabled!
- There is **no completion banner** offering:
  - `[+ Log Next Deviation / Upload Next Document]`
  - `[Download Regulatory Summary]`
  - `[View in Audit Trail]`

### B. The Non-Functional "Save Deviation" Button (BUG-02 & BUG-03)
In `DeviationFormPanel.jsx`:
```jsx
<button
  className="btn btn-success"
  disabled={status !== 'committed'}
  title={status !== 'committed' ? 'Complete the AI assessment confirmation first' : 'Deviation committed'}
>
  {status === 'committed' ? <><CheckCircle2 size={16} /> Committed</> : <><Save size={16} /> Save Deviation</>}
</button>
```
1. Notice the total lack of `onClick`. Even if enabled, pressing it does nothing.
2. The condition `disabled={status !== 'committed'}` is inverted logic: you can only click Save *after* it's already committed? And when it *is* committed, it says "Committed" and is disabled!
3. If a human operator manually types all 7 required fields:
   - `site_plant`
   - `date_of_occurrence`
   - `title`
   - `source`
   - `detailed_description`
   - `initial_impact`
   - `initial_severity`
   They are **100% blocked** because `status` will stay `pending_triage` or `idle` forever without an AI interaction.

### C. Groq Model & JSON Parser Fragility (BUG-06)
In `app/graph/nodes.py`:
```python
def _parse_json_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        ...
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
```
Groq LLMs (`openai/gpt-oss-120b` or `llama-3.3-70b-versatile`) frequently respond with:
> "Certainly! Here is the extracted JSON for the deviation report:
> ```json
> { ... }
> ```"

Because the text starts with `"Certainly!"`, `cleaned.startswith("```")` is `False`. `json.loads` throws `JSONDecodeError`, returning `{}`. The user perceives this as "The AI assistant is not working or failing randomly."

### D. Field Synchronization Disconnect (BUG-04)
When a user edits an input field in `DeviationFormPanel.jsx`:
- `handleFieldChange` dispatches `updateFieldManually` to Redux `draftSlice`.
- **Zero HTTP requests are sent to the backend**.
- The backend `_draft_store[draft_id]["fields"]` remains empty.
- When the user asks the chat: *"What is the batch number?"* or *"Change the title to X"*, the AI graph reads the backend's empty `current_fields` and hallucinates or reports missing data.

---

## 3. The Comprehensive Architectural Solution

### Pillar 1: Seamless Multi-File & Continuous Pipeline
1. **Post-Commit Success Modal / Workflow Bar**:
   - As soon as a deviation is committed, display a sleek compliance confirmation banner:
     - **"Deviation #DEV-2026-XXXX Committed & Locked"**
     - Primary Action: **`+ Log Next Deviation / Process Next File`**
     - Secondary Action: **`View Full Audit Trail`**
2. **Instant Pipeline Reset Function (`startNextDeviation`)**:
   - Calls `createDraft()` API to obtain a fresh UUID.
   - Resets form state, clears chat messages, and restores the upload dropzone and chat input.
   - Operator can immediately drop File #2, File #3, etc., without refreshing the browser!

### Pillar 2: Active Two-Way Save & Commit Engine
1. **Direct Form Submission Route (`POST /api/drafts/{id}/commit`)**:
   - Accepts the complete state of the form (all 9 fields + reviewer info).
   - Validates that required fields are present.
   - Updates the database, records human audit trail events, and marks the deviation as `committed`.
2. **Direct Manual Field Synchronization Route (`PATCH /api/drafts/{id}/fields`)**:
   - Persists manual edits from the form directly into `_draft_store` and database.
   - Logs `actor="human"` audit entries in `deviation_events`.
3. **Active `Save Deviation` Button in `DeviationFormPanel.jsx`**:
   - Enabled whenever all required fields are filled.
   - If an AI assessment is pending, it prompts or handles confirmation.
   - If all fields were filled manually, it directly commits the deviation and advances the pipeline.

### Pillar 3: Resilient Multi-Pattern JSON Parser
Enhance `_parse_json_response`:
1. Direct `json.loads` attempt.
2. Regex extraction for markdown code blocks (````(?:json)?\s*([\s\S]*?)\s*````).
3. Balanced bracket scan: finding the first `{` and last `}` in the string.
4. Trailing comma cleanup regex for robust parsing against small LLM syntax quirks.

### Pillar 4: Flexible Risk Assessor Triggering
In `builder.py`:
- Allow risk assessment if `detailed_description` is present, even if `title` is missing (generating a synthesized title if needed).
- Allow manual fields to trigger risk assessment on demand via chat (*"Assess risk"*).

---

## 4. Implementation Checklist

- [x] **Backend Schema**: Add `DraftFieldUpdateRequest` and `DirectCommitRequest` to `app/schemas.py`.
- [x] **Backend Endpoints**: In `app/routers/drafts.py`, implement `PATCH /{draft_id}/fields` and `POST /{draft_id}/commit`, and update `confirm_assessment` to handle direct commits with full fields and include `date_of_occurrence`.
- [x] **Backend Parser**: Upgrade `_parse_json_response` in `app/graph/nodes.py` to multi-pattern extraction (direct parse, markdown code fences, outer balanced braces, and trailing comma recovery).
- [x] **Backend Prompts**: Add `initial_severity` and `initial_impact` to `PATCH_SYSTEM_PROMPT` in `app/graph/prompts.py`.
- [x] **Frontend API Slice**: Add `updateDraftFields` and `commitDirect` mutations to `apiSlice.js`.
- [x] **Frontend Form Panel**: Wire active `handleSaveDeviation` with validation feedback, enable "Log Next Deviation" when committed, and fix Reset Form.
- [x] **Frontend Copilot Panel**: Display celebratory post-commit banner with `+ Log Next Deviation / Process Next File` CTA and sticky bottom action bar.
- [x] **Verification**: Run complete test suite (23/23 tests passing) and validated production frontend build with Vite.

