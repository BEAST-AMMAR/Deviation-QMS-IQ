# Roadmap
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
A build order with exit criteria per phase — so progress is measured by "does this
verifiably work" rather than "how much time has passed." Effort estimates below are
planning estimates, not measured data.

### 2. Why this order (contract-first)
Schemas and DB models are built before any application code that depends on them, and the
AI core is proven correct *before* the frontend is wired to it. This prevents the most
common integration failure in fast AI-app builds: a frontend guessing at a response shape
that the backend/AI layer later changes. See `08_TDD` §1.

### 3. Phases

| Phase | Deliverable | Exit criteria | Est. effort |
|---|---|---|---|
| 0 — Contract design | Pydantic schemas, DB DDL, API contract frozen (this doc set) | All schemas reviewed and agreed before code starts | 1–2 hrs |
| 1 — Backend foundation | FastAPI skeleton, SQLAlchemy models, Alembic migration applied, Docker Compose running Postgres | `docker compose up` brings up an empty, correctly-shaped DB | 2 hrs |
| 2 — AI core + eval harness | LangGraph graph (all nodes), 6–8 synthetic test deviations, offline accuracy check | Extraction/risk-assessment nodes pass the eval set without touching a UI | 3–4 hrs |
| 3 — API layer | FastAPI routes wrapping the graph, incl. interrupt/resume endpoints | All endpoints in `08_TDD` §5 callable via curl/Postman | 2 hrs |
| 4 — Frontend shell | React+RTK layout matching `10_UIUX`, wired to a backend already proven correct | Two-panel layout renders; static states match wireframes | 2–3 hrs |
| 5 — Integration | Live extraction, correction, confirmation-card, commit flow end-to-end | UC-01 through UC-07 all pass manually | 2–3 hrs |
| 6 — Audit trail + polish | Audit drawer, confidence/highlight styling, reset flow | US-06 satisfied; visual states match `10_UIUX` §3 | 1–2 hrs |
| 7 — Test pass | Run `15_Test_Plan.md` checklist in full | No blocking defects remain | 1–2 hrs |
| 8 — Demo production | Record both required videos | Videos match assessment's exact requested content | 1–2 hrs |

### 4. Critical path
Phase 2 (AI core) is the highest-risk phase and gates everything downstream — if the
extraction schema changes after Phase 4 starts, expect rework in both frontend and backend.
Do not start Phase 4 until Phase 2's eval harness passes.

### 5. Definition of "ready to submit"
All `01_BRD` §6 success criteria true, both demo videos recorded per the assessment's exact
content requirements, submission form completed, and no assignment/code/video pushed to
any public repository (`01_BRD` §4).
