# Security Policy & GxP Vulnerability Disclosure

## 1. Scope & Commitment

DeviationIQ is an enterprise pharmaceutical deviation intake system operating under **FDA 21 CFR Part 11**, **ICH Q9/Q10**, and **GAMP 5** guidelines. We treat data integrity, electronic signature fidelity, and anti-hallucination controls as critical safety requirements.

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability or potential data integrity breach, please report it privately:

- **Email**: `security@aivoa.ai`
- **PGP Key**: Available upon request
- **Response SLA**: Initial triage within 24 hours; technical remediation plan within 72 hours.

**Please do not open public GitHub issues for security vulnerabilities.**

---

## 3. Core Architectural Defenses

| Security Layer | Technical Control | Regulatory Mapping |
|:---|:---|:---|
| **Prompt Injection Defense** | Incident report content is treated exclusively as untrusted data, isolated inside distinct demarcation fences. The LLM is explicitly forbidden from following embedded instructions. | ICH Q9 Risk Control |
| **Zero-Fabrication Constraint** | Missing attributes strictly yield `null` values with low confidence markers. Hallucination is actively guarded via structured schema validation. | 21 CFR §11.10(a) Validation |
| **Human Confirmation Gate** | Risk severity proposals cannot mutate persistent regulatory records without explicit human officer review and digital sign-off. | 21 CFR §11.50 Attribution |
| **Append-Only Event Ledger** | All field changes record verbatim prior/new values, timestamps, and actor attributions (`ai` vs `human`) with zero UPDATE/DELETE REST endpoints. | ALCOA+ Audit Trail |
| **Secrets Hygiene** | API keys, database credentials, and signing tokens must never be checked into source control. Managed exclusively through environment variables. | ISO 27001 / OWASP Top 10 |

---

## 4. Supported Versions

| Version | Supported | Security Patches |
|:---|:---:|:---|
| 1.0.x (Current) | ✅ Yes | Active monthly updates |
| < 1.0.0 | ❌ No | Deprecated |

