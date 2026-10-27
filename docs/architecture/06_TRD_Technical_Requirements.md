# Technical Requirements Document (TRD)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
The SRS says *what* the system must do; this document says *what it must be built with* —
exact stack, versions, and environment — so an engineer (human or AI coding agent) never
has to guess a version or substitute a library.

### 2. Stack (locked vs. chosen)
| Component | Requirement | Locked by assessment? |
|---|---|---|
| Frontend framework | React 18+ | Yes |
| Frontend state | Redux Toolkit (RTK) + RTK Query | Partially — "Redux" mandated; RTK is the chosen modern implementation |
| Backend framework | FastAPI (Python 3.11+) | Yes |
| AI orchestration | LangGraph (current stable release) | Yes |
| LLM provider | Groq | Yes |
| Database | PostgreSQL 15+ | Choice within "PostgreSQL/MySQL" option — see §3 |
| ORM | SQLAlchemy 2.0 (async) + Alembic migrations | Chosen |
| PDF parsing | `pdfplumber` | Chosen |
| Containerization | Docker + Docker Compose | Chosen |

### 3. Model selection reasoning
The assessment brief suggests `gemma2-9b-it` or `llama-3.3-70b-versatile`. **`gemma2-9b-it`
is deprecated on Groq's production model catalog as of this build** — Groq's own
documentation recommends migrating off it. This TRD therefore specifies:
- **`llama-3.3-70b-versatile`** — primary model for extraction and risk-assessment nodes
  (strong reasoning on messy/ambiguous incident text, reliable structured-JSON output).
- **A smaller/faster Groq model** (e.g., an 8B-class instant model) — used only for the
  cheap "is this new content or a correction?" routing classification, to avoid paying
  70B-model latency/cost for a one-word decision.

Model names on Groq's catalog change; whichever build agent implements this should check
`https://console.groq.com/docs/models` at build time and substitute the current production
equivalent if either named model has been retired.

### 4. Environment requirements
| Requirement | Value |
|---|---|
| Node.js | 20 LTS+ |
| Python | 3.11+ |
| PostgreSQL | 15+ |
| Docker / Docker Compose | Current stable |
| Groq API key | Required, environment variable `GROQ_API_KEY`, never hardcoded |

### 5. Third-party dependencies (backend)
`fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic` v2,
`langgraph`, `langgraph-checkpoint-postgres`, `groq` (official SDK), `pdfplumber`,
`python-multipart` (file upload support).

### 6. Third-party dependencies (frontend)
`react`, `react-dom`, `@reduxjs/toolkit`, `react-redux`, standard build tooling (Vite
recommended for build speed over CRA).

### 7. Non-functional technical constraints
- Requires live internet access at runtime (Groq API is remote; no offline mode).
- Not designed for horizontal scaling or multi-tenant isolation in this build (see
  `01_BRD` §4 out-of-scope).
- Secrets managed via `.env` file (git-ignored) plus a committed `.env.example`.
