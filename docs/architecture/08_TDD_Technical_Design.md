# Technical Design Document (TDD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
The SAD explains the shape of the system; this document is the detailed, implementation-
level design — schemas, node signatures, and API contracts precise enough that a developer
(or an AI coding agent) can build against it without re-deciding structure mid-build. This
is deliberately written *before* any application code, per the "contract-first" approach
in `12_Roadmap.md` §2.

### 2. Pydantic schemas (shared contract — backend and AI layer)
```python
from typing import Literal, Optional
from pydantic import BaseModel

class ExtractedField(BaseModel):
    value: Optional[str]
    confidence: Literal["high", "medium", "low"]
    source_snippet: Optional[str]

class DeviationExtraction(BaseModel):
    site_plant: ExtractedField
    date_of_occurrence: ExtractedField
    title: ExtractedField
    source: ExtractedField
    related_product: ExtractedField
    batch_lot: ExtractedField
    detailed_description: ExtractedField

class RiskAssessment(BaseModel):
    suggested_severity: Literal["Minor", "Major", "Critical"]
    suggested_impact: str
    reasoning: str
```

### 3. LangGraph state
```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class DraftState(TypedDict):
    draft_id: str
    raw_input: str
    current_fields: dict           # last known field values + metadata
    messages: Annotated[list, add_messages]
    pending_assessment: Optional[RiskAssessment]
```

### 4. Node design
| Node | Model | Input | Output | Notes |
|---|---|---|---|---|
| `router` | small/fast Groq model | latest message + `current_fields` presence | `"extract" \| "correct" \| "chitchat"` | Cheap classification only |
| `extractor` | `llama-3.3-70b-versatile` | `raw_input` | `DeviationExtraction` | Structured/JSON-mode output; prompt instructs "return null for unknown, never invent" (enforces NFR-03) |
| `risk_assessor` | `llama-3.3-70b-versatile` | `current_fields` | `RiskAssessment` | Runs only once required extraction fields are present |
| *(interrupt point)* | — | `pending_assessment` | human decision | `interrupt()` call; graph pauses here, checkpointed |
| `patch_node` | `llama-3.3-70b-versatile` | correction message + `current_fields` | diff of changed fields only | Never rewrites fields not mentioned |
| `committer` | — | confirmed assessment | DB write | Writes `deviations` + `deviation_events` |
| `responder` | — | node outputs | natural-language chat reply | Names exactly which fields changed |

### 5. API contract (FastAPI)
| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| POST | `/drafts` | Create a new draft | — | `{draft_id}` |
| POST | `/drafts/{id}/message` | Send pasted text or a chat message | `{text}` | `{fields, chat_reply}` |
| POST | `/drafts/{id}/upload` | Upload a file for extraction | multipart file | `{fields, chat_reply}` |
| GET | `/drafts/{id}` | Fetch current draft state | — | `{fields, status, messages}` |
| POST | `/drafts/{id}/confirm` | Resume graph past the interrupt with confirmed/edited assessment | `RiskAssessment` | `{status: "committed", deviation_id}` |
| GET | `/deviations/{id}` | Fetch a committed, read-only record | — | full record + audit trail |
| GET | `/deviations/{id}/events` | Fetch the audit trail | — | list of `deviation_events` rows |
| POST | `/drafts/{id}/reset` | Discard draft | — | `{status: "reset"}` |

### 6. Frontend design (Redux Toolkit)
- **`draftSlice`** — form field values + per-field `{confidence, source_snippet, origin:
  'ai'|'human'}` metadata + status (`pending_triage` / `ready_to_commit` / `committed`).
- **`chatSlice`** — message list, loading/in-flight state.
- **RTK Query API slice** — endpoints matching §5 exactly (`useSendMessageMutation`,
  `useUploadFileMutation`, `useConfirmAssessmentMutation`, etc.) — this is what prevents
  the frontend from drifting from the backend contract, since both reference the same
  endpoint shapes.
- **Component tree:**
  ```
  App
  ├─ DeviationFormPanel
  │   ├─ FormSection (×N, one per field group)
  │   └─ StatusBadge
  ├─ AICopilotPanel
  │   ├─ UploadDropzone
  │   ├─ ChatThread
  │   ├─ ConfirmationCard   (renders during the interrupt/pending_assessment state)
  │   └─ ChatInput
  └─ AuditTrailDrawer
  ```

### 7. Prompt design notes
Extraction and risk-assessment prompts must explicitly state: (1) return `null` rather
than a guess for any field not clearly present in the source text, (2) quote the exact
source phrase for `source_snippet` rather than paraphrasing, (3) never reference
information outside the provided input text. This directly implements NFR-03 and is the
primary defense discussed in `14_Security_Plan.md` §3.
