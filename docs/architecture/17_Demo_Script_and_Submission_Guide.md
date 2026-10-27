# Demo Video Scripts & Final Submission Guide
## AIVOA.AI — AI-Powered Deviation Intake Module

---

### 1. Pre-Recording Regression Checklist

Before opening screen recording software (e.g. OBS, Loom), verify each item:

- [x] Backend running on `http://localhost:8000` (FastAPI + Swagger Docs live)
- [x] Frontend running on `http://localhost:5173` (React 19 + Redux Toolkit live)
- [x] Groq API connected and verified with active models (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`)
- [x] All 18 pytest tests passing (`.venv\Scripts\pytest.exe -v tests`)
- [x] AI offline evaluation harness passing at 86% match / 100% null accuracy (`.venv\Scripts\python.exe -m app.eval.run_eval`)
- [x] Browser window set to clean 1080p full-screen with dark theme enabled
- [x] Sample deviation text copied to clipboard

---

### 2. Video 1: End-to-End Workflow Demonstration (5–8 Minutes)

#### **Goal**
Demonstrate the complete pharmaceutical deviation intake workflow from raw unstructured input to committed, immutable GxP record.

#### **Scene 1: Introduction & Problem Context (0:00 – 1:00)**
* **Visual**: Show the clean, empty AIVOA.AI Deviation Logging screen (`http://localhost:5173`).
* **Talking Points**:
  > *"Hello, I'm Muhammad Ammar. In pharmaceutical manufacturing under FDA 21 CFR Part 11 and GAMP 5, logging deviations accurately is critical. Traditionally, operators spend hours manually copying information from incident emails, shift logs, or calibration reports into QMS forms. This manual entry leads to errors and incomplete data. Today I'm demonstrating the AIVOA.AI Deviation Intake Module — an AI-powered system designed with strict human oversight, anti-hallucination guardrails, and immutable audit trails."*

#### **Scene 2: Ingesting an Incident Report (1:00 – 2:30)**
* **Visual**: Paste the sample temperature excursion text into the AI Deviation Assistant chat box and click **Send**.
* **Text to Paste**:
  ```text
  Subject: Deviation Report — Temperature Excursion in Reactor R-201
  Date: September 15, 2026
  Site: Hyderabad API Plant, Building B2

  During the synthesis of Intermediate Compound IPC-7 (Batch HYD-2026-0842), 
  the temperature in Reactor R-201 was recorded at 78.3°C at 14:22 IST, which 
  exceeds the approved specification limit of 72 ± 2°C for the condensation step.

  The operator on duty, Technician Priya Sharma, immediately initiated the 
  emergency cooling protocol per SOP-MFG-042 Rev.3. Temperature returned to 
  within specification (71.8°C) at 14:47 IST, approximately 25 minutes after 
  the initial excursion.

  Product involved: Atorvastatin Calcium API
  Source: Shift Log Entry #SL-2026-0915-B
  ```
* **Visual Action**: Point out the fields auto-populating on the left panel.
* **Talking Points**:
  > *"Notice how the left form immediately populates with zero manual typing:*
  > * - Site: Hyderabad API Plant, Building B2*
  > * - Date: 2026-09-15*
  > * - Product: Atorvastatin Calcium API*
  > * - Batch: HYD-2026-0842*
  > * - Detailed Description with exact temperature excursion values*
  > *Notice the visual confidence badges: every field is marked with its confidence level ('High') and origin ('AI') with exact source snippet provenance."*

#### **Scene 3: Natural Language Field Correction (2:30 – 3:45)**
* **Visual**: In the chat box, type a correction message:
  ```text
  Actually, the batch number was corrected to HYD-2026-0843 per the QA supervisor.
  ```
* **Visual Action**: Press **Send**. Show that only the `Batch / Lot Number` updates to `HYD-2026-0843` and its origin badge flips from `AI` to `Human`. All other fields remain unchanged.
* **Talking Points**:
  > *"Under pharmaceutical change control, an AI should never re-write fields that weren't mentioned. Notice that our patch node selectively updated only the batch number, while all other previously extracted fields remained intact."*

#### **Scene 4: The Human-in-the-Loop Confirmation Gate (3:45 – 5:15)**
* **Visual**: Highlight the **AI Risk Assessment Confirmation Card** that appeared in the chat thread. Point out:
  * Suggested Severity: `Major`
  * Clinical Reasoning: Temperature exceeded specification limit by 6.3°C for 25 minutes during active condensation.
* **Visual Action**: Show that the **Save Deviation** button is disabled until human confirmation is complete.
* **Talking Points**:
  > *"This is our LangGraph interrupt gate — a critical regulatory safeguard. AI can propose risk classifications, but FDA compliance requires an authorized human to confirm. We can either accept the suggested 'Major' severity or adjust it. I'll enter my review signature 'Dr. Sarah Lin (QA Lead)' and click 'Confirm & Commit Assessment'."*
* **Visual Action**: Click **Confirm Assessment**. Show that the form unlocks and the status changes to committed.

#### **Scene 5: 21 CFR Part 11 Audit Trail & Read-Only Enforcement (5:15 – 6:30)**
* **Visual**: Click the **Audit Trail** button in the bottom action bar. The slide-out drawer opens.
* **Talking Points**:
  > *"Clicking Audit Trail opens our append-only ledger. Notice every single transaction is recorded:*
  > * - Initial AI extractions with source snippet quotes*
  > * - Human correction of the batch number*
  > * - Human confirmation of the Major severity with timestamp and reviewer identity*
  > *Once committed, the record is strictly read-only at the API level (HTTP 409 Conflict on modification attempts), satisfying 21 CFR Part 11 data integrity requirements."*

---

### 3. Video 2: Architecture & Code Walkthrough (5–8 Minutes)

#### **Goal**
Walk through the architectural design, directory structure, and technical decisions that make the system production-grade.

#### **Scene 1: Architecture Big Picture (0:00 – 1:30)**
* Open [`README.md`](file:///d:/projects/AIVOI/README.md) or [`07_SAD_System_Architecture.md`](file:///d:/projects/AIVOI/aivoa_docs/07_SAD_System_Architecture.md).
* **Talking Points**:
  > *"For the architecture, we adopted a contract-first approach with three decoupled layers:*
  > * 1. React 19 + Redux Toolkit frontend using RTK Query to eliminate contract drift.*
  > * 2. FastAPI backend providing stateless REST endpoints with async SQLAlchemy.*
  > * 3. LangGraph AI state machine with multi-model routing (Fast 20B classifier + Large 120B extractor).*
  > * 4. Dual persistence: PostgreSQL for production Docker, with zero-config automatic SQLite fallback for local development."*

#### **Scene 2: Data Contracts & Single Source of Truth (1:30 – 2:45)**
* Open [`backend/app/schemas.py`](file:///d:/projects/AIVOI/backend/app/schemas.py) and [`backend/app/models.py`](file:///d:/projects/AIVOI/backend/app/models.py).
* **Talking Points**:
  > *"Notice `schemas.py`. This is the single source of truth across the frontend, backend, and AI graph. Column names match the database DDL and functional requirements exactly. In `models.py`, we have the primary `Deviation` record, the append-only `DeviationEvent` audit ledger, and raw `AIExtractionLog` for offline evaluation."*

#### **Scene 3: The LangGraph State Machine & Guardrails (2:45 – 4:15)**
* Open [`backend/app/graph/builder.py`](file:///d:/projects/AIVOI/backend/app/graph/builder.py) and [`backend/app/graph/nodes.py`](file:///d:/projects/AIVOI/backend/app/graph/nodes.py).
* **Talking Points**:
  > *"Here is the StateGraph builder:*
  > * - `router_node`: Uses a fast small model to classify intent into `extract`, `correct`, or `chitchat`.*
  > * - `extractor_node`: Extracts structured data using system prompts fortified against prompt injection. Rule 1 strictly enforces that user input is treated as DATA ONLY, never instructions.*
  > * - `risk_assessor_node`: Formulates the clinical risk proposal.*
  > * - `patch_node`: Computes selective field diffs for corrections.*
  > *Notice that we enforce safe 12,000-character chunking to prevent token-overflow errors on large multi-page PDF reports."*

#### **Scene 4: Offline AI Evaluation Harness & Pytest (4:15 – 5:30)**
* Open terminal and show:
  * Pytest: `.venv\Scripts\pytest.exe -v tests` (18 passing tests)
  * Eval Harness: `.venv\Scripts\python.exe -m app.eval.run_eval`
* **Talking Points**:
  > *"In pharma AI, unit testing isn't enough — you need systematic AI evaluation. We built an offline evaluation harness against 6 hand-labeled synthetic test cases covering emails, terse shift notes, PDF text, ambiguous reports with missing fields, and embedded prompt-injection attacks. Our harness runs at 86% extraction match with 100% zero-hallucination null-correctness."*

---

### 4. Assessment Submission Form Responses

When completing the submission Google Form, emphasize these three key evaluation criteria:

1. **Product Judgment**:
   * Decoupled the workflow: AI *assists* by extracting and suggesting, but a human *confirms* via an explicit interrupt gate before saving.
   * Marked field confidence and source snippet provenance so operators can verify AI outputs in seconds without blind trust.
2. **AI Engineering**:
   * Small model for cost-effective routing + Large model for high-precision extraction.
   * Robust anti-injection defenses and null-extraction rules (FR-07: never fabricate unknown data).
   * Offline evaluation harness measuring quantitative extraction and hallucination metrics.
3. **Full-Stack Execution**:
   * Strict contract-first design with Pydantic v2 and SQLAlchemy 2.0.
   * 21 CFR Part 11 append-only audit trail and read-only enforcement.
   * Zero-config resilience: works out of the box with Docker Compose or standalone with automatic SQLite fallback.
