# AIVOA.AI — DeviationIQ Documentation Suite
## Master Documentation Index & Technical Navigation Guide

This directory houses the comprehensive enterprise and regulatory documentation suite for **DeviationIQ** — an AI-Powered Pharmaceutical Deviation Intake Module engineered in strict compliance with **FDA 21 CFR Part 11**, **ICH Q9/Q10**, and **GAMP 5** standards.

---

## 📂 Documentation Directory Structure

```
docs/
├── README.md                            # Master index and navigation guide (this file)
│
├── reports/                             # Publication-Grade Reports (PDF & Markdown)
│   ├── DeviationIQ_Technical_Report.pdf # 38-page comprehensive technical project report
│   ├── DeviationIQ_Technical_Report.md  # Markdown source for technical report
│   ├── Pipeline_Explainer.pdf           # 9-page two-way engineering & pitch guide
│   └── Pipeline_Explainer.md            # Markdown source for pipeline explainer
│
├── architecture/                        # Formal GxP Specifications & Architectural Deliverables
│   ├── 01_BRD_Business_Requirements.md
│   ├── 02_PD_Project_Charter.md
│   ├── 03_PRD_Product_Requirements.md
│   ├── 04_FRD_Functional_Requirements.md
│   ├── 05_SRS_Software_Requirements_Specification.md
│   ├── 06_TRD_Technical_Requirements.md
│   ├── 07_SAD_System_Architecture.md
│   ├── 08_TDD_Technical_Design.md
│   ├── 09_Database_Schema_and_ER.md
│   ├── 10_UIUX_Wireframes_and_Design.md
│   ├── 11_User_Stories_and_Use_Cases.md
│   ├── 12_Roadmap.md
│   ├── 13_Risk_Management_Log.md
│   ├── 14_Security_Plan.md
│   ├── 15_Test_Plan.md
│   ├── 16_QAP_Quality_Assurance_Plan.md
│   └── 17_Demo_Script_and_Submission_Guide.md
│
└── audit/                               # Quality, Usability & Remediation Logs
    └── codebase_audit_and_remediation_plan.md
```

---

## 📑 1. Executive & Technical Reports

| Document | Format | Description | Target Audience |
|:---|:---:|:---|:---|
| [DeviationIQ_Technical_Report.pdf](reports/DeviationIQ_Technical_Report.pdf) | PDF (38p) | Complete technical project report covering 15 chapters: architecture, state machine, data models, endpoints, security, and verification. | Technical Directors, Auditors, System Architects |
| [DeviationIQ_Technical_Report.md](reports/DeviationIQ_Technical_Report.md) | Markdown | Raw source manuscript for the comprehensive technical project report. | Developers, Technical Writers |
| [Pipeline_Explainer.pdf](reports/Pipeline_Explainer.pdf) | PDF (9p) | Two-way architectural breakdown: Section A (Pointwise Technical) and Section B (Conversational Executive Pitch). | Engineering Leads & Product Stakeholders |
| [Pipeline_Explainer.md](reports/Pipeline_Explainer.md) | Markdown | Raw source manuscript for the two-way pipeline explainer document. | Developers, Sales Engineers |

---

## 🏛️ 2. Architectural & Regulatory Specifications

| # | Specification Document | Key Domain | Primary Questions Answered |
|:---:|:---|:---|:---|
| 01 | [01_BRD_Business_Requirements.md](architecture/01_BRD_Business_Requirements.md) | Business Strategy | *Why does this module exist? What ROI does automated deviation logging deliver?* |
| 02 | [02_PD_Project_Charter.md](architecture/02_PD_Project_Charter.md) | Governance | *What are project milestones, boundaries, resource commitments, and delivery goals?* |
| 03 | [03_PRD_Product_Requirements.md](architecture/03_PRD_Product_Requirements.md) | Product Management | *Who are the personas, core user stories, functional gates, and UX metrics?* |
| 04 | [04_FRD_Functional_Requirements.md](architecture/04_FRD_Functional_Requirements.md) | Functional Scope | *What are the itemized, testable capabilities for field extraction and confirmation?* |
| 05 | [05_SRS_Software_Requirements_Specification.md](architecture/05_SRS_Software_Requirements_Specification.md) | Formal Engineering | *The single authoritative system specification (Functional & Non-Functional).* |
| 06 | [06_TRD_Technical_Requirements.md](architecture/06_TRD_Technical_Requirements.md) | Technical Stack | *What runtimes, dependency versions, API schemas, and platforms are mandated?* |
| 07 | [07_SAD_System_Architecture.md](architecture/07_SAD_System_Architecture.md) | Architecture | *How do the three tiers interact? Why was LangGraph state machine selected?* |
| 08 | [08_TDD_Technical_Design.md](architecture/08_TDD_Technical_Design.md) | Detailed Design | *Node-by-node state transitions, endpoint payloads, error handling, and reducers.* |
| 09 | [09_Database_Schema_and_ER.md](architecture/09_Database_Schema_and_ER.md) | Data Persistence | *PostgreSQL & SQLite schema definitions, indexing, constraints, and audit tables.* |
| 10 | [10_UIUX_Wireframes_and_Design.md](architecture/10_UIUX_Wireframes_and_Design.md) | Frontend / UX | *Design tokens, field badges, confirmation cards, and responsive component states.* |
| 11 | [11_User_Stories_and_Use_Cases.md](architecture/11_User_Stories_and_Use_Cases.md) | QA / Product | *Step-by-step acceptance criteria for incident ingestion, patching, and triage.* |
| 12 | [12_Roadmap.md](architecture/12_Roadmap.md) | Delivery Tracking | *Phased milestone breakdown, task sequencing, and project completion criteria.* |
| 13 | [13_Risk_Management_Log.md](architecture/13_Risk_Management_Log.md) | GxP Risk (ICH Q9) | *Risk matrix, failure mode analysis (FMEA), mitigations, and safety fallbacks.* |
| 14 | [14_Security_Plan.md](architecture/14_Security_Plan.md) | Cybersecurity | *Prompt injection defense, data encryption, 21 CFR Part 11 integrity controls.* |
| 15 | [15_Test_Plan.md](architecture/15_Test_Plan.md) | Verification | *Unit, integration, regression, and offline LLM evaluation harness specifications.* |
| 16 | [16_QAP_Quality_Assurance_Plan.md](architecture/16_QAP_Quality_Assurance_Plan.md) | Quality System | *Code review guidelines, static analysis criteria, and definition of done.* |
| 17 | [17_Demo_Script_and_Submission_Guide.md](architecture/17_Demo_Script_and_Submission_Guide.md) | Evaluation & Demo | *Video submission walk-through, demo scripts, and assessor presentation outline.* |

---

## 🔍 3. Quality & Remediation Logs

- [codebase_audit_and_remediation_plan.md](audit/codebase_audit_and_remediation_plan.md): Comprehensive architectural, pipeline, and usability audit identifying root causes for the 7 historical workflow friction points (BUG-01 to BUG-07) and documenting all verified fixes.

---

## 🛠️ Rebuilding the PDF Reports

To recompile the PDF reports from their Markdown source with vector Mermaid diagrams and GxP headers:

```bash
# Run from repository root:
python scripts/build_reports.py
```
Outputs are automatically written to `docs/reports/`.
