# System Architecture Document (SAD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
This document shows how the pieces from the TRD are arranged and *why* — the reasoning
behind each architectural decision, condensed from the full design debate so it can be
defended in an interview or code-walkthrough video without re-deriving it live.

### 2. Context diagram
```
   Quality Officer
        │
        ▼
 ┌─────────────────┐        HTTPS         ┌────────────────┐
 │   Web Browser     │ ───────────────────▶ │  This System    │
 │ (React SPA)        │ ◀─────────────────── │ (Frontend+API)  │
 └─────────────────┘                       └────────┬────────┘
                                                     │ HTTPS
                                                     ▼
                                             ┌────────────────┐
                                             │   Groq API      │
                                             │ (LLM inference) │
                                             └────────────────┘
```

### 3. Container diagram
```
┌───────────────────────────────────────────────────────────────────┐
│  React + Redux Toolkit + RTK Query (SPA)                            │
│  DeviationFormPanel │ AICopilotPanel │ AuditTrailDrawer               │
└──────────────────────────────┬────────────────────────────────────┘
                                │ REST/JSON
┌──────────────────────────────▼────────────────────────────────────┐
│  FastAPI application                                                │
│  routers: drafts, uploads, confirmations, deviations (committed)    │
└──────────────────────────────┬────────────────────────────────────┘
                                │
┌──────────────────────────────▼────────────────────────────────────┐
│  LangGraph StateGraph  (checkpointer: PostgresSaver, thread_id =      │
│  draft_id)                                                            │
│  router → extractor → risk_assessor → interrupt() → committer         │
│  router → patch_node → responder   (correction path)                  │
└──────────────────────────────┬────────────────────────────────────┘
                                │
┌──────────────────────────────▼────────────────────────────────────┐
│  PostgreSQL                                                          │
│  deviations │ deviation_events │ ai_extraction_log │ langgraph_checkpoints │
└───────────────────────────────────────────────────────────────────┘
```

### 4. Key architectural decisions and reasoning

**Decision: LangGraph `interrupt()` + `Command(resume=...)` as the commit gate, not a
plain "Save" button hitting a REST endpoint directly.**
Reasoning: a regulated deviation record's severity classification must have explicit human
sign-off before it's written (see `01_BRD` §3, BO-2). Modeling this as a graph-level
interrupt — rather than trusting the frontend to "remember" to show a confirmation dialog —
makes the confirmation structurally required at the orchestration layer, not just a UI
convention that a future change could accidentally remove. This requires a **persistent**
checkpointer (`PostgresSaver`), because a human may take real time to review before
resuming — an in-memory checkpointer would lose the paused state on a backend restart.

**Decision: event-sourced audit log (`deviation_events`) instead of only overwriting
columns in place.**
Reasoning: ALCOA+ (`01_BRD` §2) requires records to be attributable and contemporaneous.
An UPDATE-only design loses the fact that the AI originally said one thing and a human
corrected it. An append-only events table preserves that history without complicating the
primary `deviations` table, which stays simple to query for current state.

**Decision: two-tier LLM usage (large model for extraction/assessment, small model for
routing).**
Reasoning: classifying "is this new content or a correction?" doesn't need a 70B-parameter
model's reasoning depth; using a smaller/faster model for that step reduces latency and
cost on the highest-frequency call, reserving the larger model for the two calls that
actually need reasoning quality.

**Decision: PostgreSQL over MySQL.**
Reasoning: native `JSONB` for storing raw AI extraction payloads and provenance data
alongside relational columns, plus first-class LangGraph checkpointer support
(`langgraph-checkpoint-postgres`) — avoids building a custom checkpoint adapter.

**Decision: `pdfplumber` over an OCR pipeline or a multimodal-vision model call.**
Reasoning: the reference demo's "OCR" label is UX framing, not a hard technical requirement
— the input documents in scope are text-based incident reports, not scanned images. Text
extraction feeding the same extractor prompt used for pasted text keeps one code path for
both input modes, which is also simpler to explain in the code-walkthrough video.

### 5. Data flow — extraction turn
1. User pastes text or uploads a file → frontend sends to `/drafts/{id}/message` or
   `/drafts/{id}/upload`.
2. Backend loads (or creates) the LangGraph thread for `draft_id`.
3. `router` node classifies intent → `extractor` node calls Groq with the
   `DeviationExtraction` schema → returns per-field `{value, confidence, source_snippet}`.
4. Response returned to frontend; Redux store updates; changed fields render with an
   AI-origin highlight.

### 6. Data flow — confirmation/commit turn
1. `risk_assessor` node runs after extraction, producing `RiskAssessment`.
2. Graph hits `interrupt()`, pausing and persisting state via `PostgresSaver`.
3. Frontend displays the suggestion in a confirm-or-edit UI; user acts.
4. Frontend calls `/drafts/{id}/confirm` with the (possibly edited) assessment.
5. Backend resumes the graph with `Command(resume=...)`; `committer` node writes to
   `deviations` (status → `committed`) and appends to `deviation_events`.

### 7. Data flow — correction turn
1. User sends a follow-up message ("actually the batch number is X").
2. `router` classifies as correction → `patch_node` diffs against current draft state,
   returning only the changed keys with fresh confidence/provenance.
3. `responder` node crafts a confirmation message naming exactly which fields changed.
4. Frontend re-highlights only those fields.
