# Quality Assurance Plan (QAP)
## AI-Powered Deviation Intake Module

### 1. Purpose of this document
Where `15_Test_Plan.md` defines *what gets tested*, this document defines the standards and
process that keep quality consistent while building — coding standards, review discipline,
and what "done" means at the code level. Useful even solo: explicit roles (`02_PD` §5) mean
you can deliberately switch hats and self-review as a different role, catching things a
single continuous mindset misses.

### 2. Coding standards
| Area | Standard |
|---|---|
| Python (backend) | PEP 8, formatted with `black`, type-hinted throughout (Pydantic models are the primary contract, so typing discipline matters more here than in a typical CRUD app) |
| JavaScript/React (frontend) | ESLint + Prettier, functional components with hooks, no class components |
| Commits | Small, descriptive, one logical change per commit |
| Naming | Field names match `04_FRD` §3 and `09_Database_Schema` exactly — no silent renaming between layers (this is what NFR-07 in `05_SRS` protects against) |

### 3. Definition of Done (per feature)
A feature is "done" only when: it satisfies its FR/US acceptance criteria, it has at least
one corresponding test from `15_Test_Plan.md`, and it matches the field/schema names
defined in the frozen contract documents (no ad-hoc field renaming mid-build).

### 4. Review process (self-review checklist, solo-build adapted)
Since one person plays every role in `02_PD` §5, review happens by deliberately switching
hats rather than skipping review:
1. As **AI/ML Engineer**: does this node's prompt still enforce "never fabricate" (NFR-03)?
2. As **Backend Engineer**: does this endpoint match `08_TDD` §5 exactly?
3. As **Frontend Engineer**: does this component read only from Redux state, per `08_TDD`
   §6, rather than holding its own drifting local copy?
4. As **QA**: does this change break any item in the `15_Test_Plan.md` §4 regression
   checklist?

### 5. Documentation standards
Every architectural decision that isn't obvious gets a one-line "why" next to it — this
document set exists specifically so that pattern continues into the code (docstrings on
LangGraph nodes explaining *why* a node exists, not just *what* it does).

### 6. Change control
Once `05_SRS_Software_Requirements_Specification.md` is treated as frozen for a given build
session, any change to a field name, endpoint shape, or table column must be reflected in
this document set before the corresponding code changes — preventing the exact drift this
whole documentation exercise was built to avoid.

### 7. Release readiness checklist
See `15_Test_Plan.md` §4 (regression checklist) combined with `12_Roadmap.md` §5
(definition of "ready to submit") — this QAP does not duplicate those lists, it points to
them as the actual release gate.
