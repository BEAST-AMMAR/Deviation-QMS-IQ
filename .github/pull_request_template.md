## Description
<!-- Provide a brief summary of the changes introduced in this Pull Request. -->

## Associated Documents & Requirements
- [ ] Maps to Functional Requirement: `FR-XX`
- [ ] Maps to Non-Functional Requirement: `NFR-XX`
- [ ] Complies with `docs/architecture/05_SRS_Software_Requirements_Specification.md`

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Regulatory / GxP compliance improvement
- [ ] Refactoring / Performance optimization
- [ ] Documentation update

## GxP & 21 CFR Part 11 Verification Checklist
- [ ] **ALCOA+ Auditability**: Any new state mutation is logged in `deviation_events` with actor attribution (`ai` or `human`).
- [ ] **Confirmation Gate**: Human review requirement is preserved before record commitment.
- [ ] **Anti-Hallucination**: Prompt templates maintain null-constraint rules for unverified fields.
- [ ] **Read-Only Invariance**: Committed deviations remain immutable at both API and UI levels.
- [ ] **Test Coverage**: All pytest unit & integration tests pass (27/27).
- [ ] **Frontend Build**: Vite production build completes cleanly with zero errors.
