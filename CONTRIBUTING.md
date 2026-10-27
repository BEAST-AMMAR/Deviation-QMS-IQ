# Contributing to DeviationIQ

Thank you for your interest in contributing to **DeviationIQ** — the AI-Powered Pharmaceutical Deviation Intake Module.

Because this project models regulated pharmaceutical quality workflows, all contributions must strictly adhere to the technical and regulatory contracts defined in [`docs/architecture/`](docs/architecture/).

---

## 1. Development Process

1. **Fork & Branch**: Create a feature branch from `master` / `main` following conventional naming:
   - `feat/feature-name`
   - `fix/bug-description`
   - `docs/doc-update`

2. **Contract-First Adherence**:
   - Schema modifications must update `backend/app/schemas.py` and `docs/architecture/09_Database_Schema_and_ER.md` concurrently.
   - Any new state mutations must log an `actor="ai"` or `actor="human"` event in `deviation_events`.

3. **Testing Standards**:
   - All backend pull requests must include unit/integration tests in `backend/tests/`.
   - Maintain 100% pass rate on existing test suites (`pytest -v backend/tests`).
   - Frontend changes must build cleanly (`npm run build` in `frontend/`).

---

## 2. Local Setup & Verification

```bash
# Backend Verification
cd backend
pytest -v tests

# Frontend Verification
cd ../frontend
npm run build
```

---

## 3. Pull Request Guidelines

Before submitting your PR:
- [ ] Confirm all 27 unit & integration tests pass.
- [ ] Confirm no `.env` or sensitive credentials are included.
- [ ] Complete the GxP & 21 CFR Part 11 checklist in `.github/pull_request_template.md`.

