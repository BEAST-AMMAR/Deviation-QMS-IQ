# Product Requirements Document (PRD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
Where the BRD justifies the project and the FRD/SRS itemize exact functions, the PRD sits
between them: it describes the product from the user's point of view — the experience,
the priority of features, and the reasoning behind UX decisions — so that when two
features compete for build time, this document says which one wins and why.

### 2. Problem statement (user-facing)
A Quality Officer receives an unstructured deviation report — a pasted email, a shift-log
note, or a scanned PDF — and currently must read it and manually type each fact into a
structured form across multiple fields, then separately judge severity/impact. This is
repetitive, slow, and easy to get subtly wrong under time pressure (e.g., mistyping a
batch number).

### 3. Target user persona
**"Priya, Quality Officer, API manufacturing plant."** Reviews 5–15 deviation reports per
shift. Not a developer. Trusts a tool more when it shows its reasoning and lets her
correct it in plain language, rather than presenting a black-box "AI decided X."

### 4. Product vision
The left-hand form is the official record. The right-hand AI panel is a copilot that
reads unstructured input and proposes the record — Priya's job shifts from *typing* to
*reviewing and correcting*, with the system always making clear which parts are AI-
suggested and unconfirmed.

### 5. Feature list (MoSCoW prioritization)
| Priority | Feature | Notes |
|---|---|---|
| **Must** | Paste-text extraction → auto-fill form | Core workflow |
| **Must** | PDF upload extraction → auto-fill form | Required input mode per assessment |
| **Must** | AI severity/impact suggestion with reasoning | Explicitly required deliverable |
| **Must** | Human confirmation gate before commit | Compliance requirement — see `07_SAD` §4 |
| **Must** | Natural-language correction of extracted fields | Explicitly required deliverable ("edit interaction tool") |
| **Must** | Save/commit to database | Core workflow |
| **Should** | Per-field confidence indicator | Builds user trust; cheap to add given the extraction schema already computes it |
| **Should** | Source-snippet provenance (why the AI picked this value) | Same reasoning as above |
| **Should** | Audit trail view of all field changes | Reinforces ALCOA+ story from `01_BRD` |
| **Could** | Streaming token-by-token fill animation | Polish only, not functional |
| **Won't (this scope)** | Multi-user roles, e-signatures, CAPA workflows | Out of scope — see `01_BRD` §4 |

### 6. UX principles
1. **Never let AI output look like a decided fact.** Unconfirmed AI fields are visually
   distinct (highlighted/bordered) from human-confirmed ones.
2. **Correction should feel conversational, not administrative.** The user should not
   have to know which specific field name to click — describing the correction in plain
   language should be enough (this is the "edit interaction tool" from the reference demo).
3. **Never fill the form by direct manual typing in the primary flow.** Per the assessment
   brief, all population goes through the AI panel — manual typing is reserved only for the
   correction path (fine-tuning after AI has already acted).
4. **Show reasoning, not just conclusions.** Every severity suggestion carries a short
   explanation string — a black-box classification is not acceptable in a compliance tool.

### 7. Non-goals
This is not a general-purpose document Q&A tool, not a multi-deviation batch importer, and
not a chatbot that answers arbitrary questions unrelated to the current draft.

### 8. Success metrics (functional, not fabricated business metrics)
See `01_BRD` §6. This PRD adds one product-specific bar: a user should be able to fully
correct a wrong AI extraction using a single natural-language message, without touching a
form field directly.
