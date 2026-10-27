# DeviationIQ — AI-Powered Deviation Intake Module

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-61DAFB.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6+-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![21 CFR Part 11](https://img.shields.io/badge/Compliance-FDA%2021%20CFR%20Part%2011-success.svg)](https://www.fda.gov/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg)](LICENSE)
[![Tests: 27 Passing](https://img.shields.io/badge/tests-27%20passing-brightgreen.svg)](backend/tests/)

An enterprise, pharmaceutical-grade Deviation Intake Module engineered in strict compliance with **FDA 21 CFR Part 11**, **ICH Q9/Q10**, and **GAMP 5** standards. The system accelerates deviation intake and incident triage while enforcing human-in-the-loop oversight, zero-hallucination guardrails, and immutable audit trails.

---

## 🏛️ Architecture Overview

The system implements a decoupled, three-tier contract-first architecture powered by an asynchronous LangGraph state machine:

```
┌─────────────────────────────────────────────────────────────┐
│                    DeviationIQ Web Interface                │
│   (React 19 + Vite + Redux Toolkit + Pharma Clinical CSS)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON (RTK Query)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Service                   │
│  - /api/drafts: In-memory session lifecycle & file triage   │
│  - /api/deviations: Read-only committed records & audit log │
│  - /api/deviations/{id}/export/pdf & docx: Dossier exports  │
│  - SecurityHeadersMiddleware (HSTS, nosniff, frame denial)  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      LangGraph Engine        │ │    PostgreSQL / SQLite     │
│  - Small Model: Router       │ │  - deviations              │
│  - Large Model:              │ │  - deviation_events (audit)│
│    • Extractor Node          │ │  - ai_extraction_logs     │
│    • Risk Assessor Node      │ └────────────────────────────┘
│    • Patch / Correction Node │
│  - Human Confirmation Gate   │
└──────────────────────────────┘
```

---

## ✨ Key Features & Regulatory Compliance

1. **Human-in-the-Loop Confirmation Gate (21 CFR Part 11 / SAD §4)**:
   - The AI risk assessor generates severity and impact proposals with clinical justification.
   - The system structurally **blocks** final deviation commitment until an authorized quality officer reviews, confirms, or modifies the assessment.

2. **Append-Only Immutable Audit Trail (ALCOA+ / FRD §3)**:
   - All state modifications are stored in the immutable `deviation_events` ledger with actor attribution (`ai` vs `human`), before/after diffs, confidence scores, and verbatim source snippets.
   - Once committed, deviations become **strictly read-only** at the API level (HTTP 409 Conflict on mutation attempts).

3. **Field-Level Confidence & AI Provenance (UIUX §3)**:
   - Visual highlighting of fields (`high`, `medium`, `low`) with expandable source snippet quotes.
   - Human manual overrides and natural language corrections cleanly transition field ownership from `ai` to `human`.

4. **Multi-Modal Document Ingestion**:
   - Supports raw text pasting and multi-format document uploads (PDF, DOCX, TXT) processed through the same validated extraction pipeline.

5. **Anti-Hallucination & Prompt Injection Defense (Security Plan §3)**:
   - System prompts enforce strict separation: user documents are treated purely as **untrusted data**, never executable instructions.
   - Null extraction constraint (FR-07): If information is not clearly present in the source text, the model returns `null` rather than fabricating values.

6. **Publication-Grade GxP Dossier Exports**:
   - Automated server-side generation of high-precision GxP **PDF** and **DOCX** deviation dossiers complete with running headers, electronic signature blocks, and audit trail diffs.

---

## 📑 Documentation & Regulatory Reports

All system specifications and publication-grade reports are organized under the [`docs/`](docs/README.md) directory:

- 📊 **[Comprehensive Technical Project Report (PDF)](docs/reports/DeviationIQ_Technical_Report.pdf)**: 38-page publication-grade specification with vector Mermaid architecture diagrams, ER diagrams, data contracts, and verification matrices.
- 🎙️ **[Pipeline Explainer Guide (PDF)](docs/reports/Pipeline_Explainer.pdf)**: 9-page two-way guide covering technical pointwise breakdowns and executive conversational pitch scripts.
- 🏛️ **[Architectural & GxP Specification Suite](docs/architecture/)**: Complete 17-document specification package (BRD, PRD, SRS, SAD, Database ER, Security Plan, Test Plan, and QAP).
- 🔍 **[Quality Audit & Remediation Log](docs/audit/codebase_audit_and_remediation_plan.md)**: Architectural and usability audit resolving historical workflow friction points (BUG-01 to BUG-07).
- 💬 **[Pair-Programming Chat History & Logs](docs/chat_history/chat_history.md)**: Formatted narrative and unabridged JSONL event logs (`transcript_full.jsonl`).

---

## 🚀 Quick Start (Development Mode)

To launch the development stack (PostgreSQL + FastAPI + React with hot-reloading):

```bash
# 1. Clone repository
git clone <your-repo-url>
cd "AIVOA project"

# 2. Configure environment variables (fill in your GROQ_API_KEY)
cp .env.example .env

# 3. Launch development containers
docker compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 🏭 Production Enterprise Deployment

For production deployments, DeviationIQ includes hardened, multi-stage containers, non-root execution, Nginx reverse proxy with gzip and security headers, and PostgreSQL persistence:

```bash
# 1. Configure production environment
cp .env.example .env
# Set secure passwords and valid GROQ_API_KEY in .env

# 2. Launch production stack
docker compose -f docker-compose.prod.yml up -d --build
```

- **Production Frontend (Nginx)**: [http://localhost](http://localhost) (Port 80)
- **Production API**: Reverse-proxied via `/api/`
- **Container Health**: Auto-restarts with automated health probes

---

## 💻 Local Development Setup (Without Docker)

### Backend Setup

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows (.venv/bin/activate on Linux/macOS)

# 2. Install dependencies
pip install -r requirements.txt
pip install aiosqlite pytest pytest-asyncio httpx markdown-it-py pymupdf

# 3. Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Run development server
npm run dev

# 3. Build production bundle
npm run build
```

---

## 🧪 Testing & Quality Assurance

### Run Backend Unit & Integration Tests (27 passing tests)

```bash
cd backend
pytest -v tests
```

Tests cover:
- Draft creation, retrieval, and reset lifecycle
- Multi-turn messaging & graph execution
- Human-in-the-loop risk confirmation gate & 409 conflict lockouts
- Direct manual field synchronization & audit trail diff tracking
- Date persistence across commits
- Multi-pattern LLM JSON extraction (preambles, markdown code fences, trailing commas)
- Router classification accuracy
- Prompt injection isolation
- GxP PDF and DOCX dossier generation
- Enterprise security headers & health endpoints

### Run AI Evaluation Harness (Test Plan §3)

```bash
cd backend
python -m app.eval.run_eval
```

Runs 6 hand-labeled synthetic test fixtures covering clean emails, terse notes, PDF documents, missing fields, prompt injection defenses, and natural language corrections.

---

## 📁 Repository Structure

```
AIVOA project/
├── .github/                             # CI/CD Workflows & Repository Governance
│   ├── workflows/ci.yml                 # Automated Pytest & Vite Build Actions
│   ├── ISSUE_TEMPLATE/                  # Bug report & feature request templates
│   └── pull_request_template.md         # GxP & 21 CFR Part 11 PR checklist
├── .env.example                         # Environment configuration template
├── .gitignore                           # Comprehensive Git exclusions
├── docker-compose.yml                   # Development orchestration (hot-reload)
├── docker-compose.prod.yml              # Production orchestration (Nginx + non-root API)
├── LICENSE                              # Apache 2.0 License
├── README.md                            # Project overview & quickstart (this file)
├── SECURITY.md                          # Vulnerability reporting & GxP disclosures
├── CONTRIBUTING.md                      # Development & review guidelines
│
├── docs/                                # Enterprise Documentation Suite
│   ├── README.md                        # Master documentation index & reading guide
│   ├── reports/                         # Publication-grade technical & executive reports
│   │   ├── DeviationIQ_Technical_Report.pdf
│   │   ├── DeviationIQ_Technical_Report.md
│   │   ├── Pipeline_Explainer.pdf
│   │   └── Pipeline_Explainer.md
│   ├── architecture/                    # Formal GxP Specifications (01_BRD to 17_Demo)
│   ├── audit/                           # Codebase audits & remediation logs
│   └── chat_history/                    # Pair-programming session history & JSONL logs
│
├── backend/                             # Python 3.11+ FastAPI + LangGraph Service
│   ├── app/
│   │   ├── config.py                    # Pydantic BaseSettings
│   │   ├── database.py                  # SQLAlchemy 2.0 Async Engine (Postgres / SQLite)
│   │   ├── models.py                    # ORM Models (Deviation, Events, AI Logs)
│   │   ├── schemas.py                   # Pydantic v2 schemas (Single source of truth)
│   │   ├── reports.py                   # PDF & DOCX regulatory export generator
│   │   ├── graph/                       # LangGraph StateGraph, Nodes & Prompts
│   │   ├── routers/                     # /api/drafts & /api/deviations endpoints
│   │   ├── services/                    # Audit logger & document parser
│   │   └── eval/                        # AI evaluation harness & fixtures
│   ├── tests/                           # Pytest suite (27 unit & integration tests)
│   ├── requirements.txt
│   ├── Dockerfile                       # Development Dockerfile
│   └── Dockerfile.prod                  # Production hardened Dockerfile (non-root)
│
├── frontend/                            # React 19 + Redux Toolkit + Vite Web App
│   ├── src/
│   │   ├── components/                  # FormPanel, CopilotPanel, ConfirmationCard, Drawers
│   │   ├── store/                       # Redux store, apiSlice, draftSlice, chatSlice
│   │   ├── index.css                    # Pharmaceutical-grade design system
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf                       # Production Nginx reverse-proxy & security config
│   ├── Dockerfile                       # Development Dockerfile
│   └── Dockerfile.prod                  # Multi-stage production Nginx Dockerfile
│
└── scripts/                             # Automation & Build Tooling
    └── build_reports.py                 # Markdown-to-PDF compilation script
```

---

## ⚖️ License & Compliance Notice

Licensed under the [Apache License, Version 2.0](LICENSE). Compliant with GAMP 5 Software Category 4, FDA 21 CFR Part 11, and ICH Q9/Q10 frameworks.
