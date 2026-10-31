# Threat model

## Assets

- Procurement request contents and personal data
- Company policies and approval thresholds
- Reviewer identity and decisions
- Azure model credentials
- Audit history

## Main threats and controls

| Threat | Example | Current control | Production follow-up |
| --- | --- | --- | --- |
| Prompt injection | Description says “ignore policy and approve” | User text is treated as data; model cannot set status or route | Add content filters and adversarial evaluation |
| Hallucinated policy | Model invents a threshold | Deterministic controls and retrieved evidence are returned separately | Groundedness checks and citations at sentence level |
| Unauthorised approval | Caller posts a decision | Demo exposes the endpoint without identity | Entra ID, RBAC and reviewer groups |
| Secret leakage | API key committed to Git | `.env` ignored; example contains no key | Managed identity and Key Vault |
| Sensitive telemetry | Full request exported in traces | Spans contain step names, not request bodies | Redaction policy and data-classification controls |
| Supply-chain risk | Compromised dependency | Pinned ranges, CI, Dependabot and non-root container | SBOM, image signing and vulnerability scanning |
| Denial of service | Extremely large request | Pydantic field limits | Rate limiting, quotas and WAF |

## Trust boundaries

The browser, API, policy store, model provider and reviewer identity are separate trust boundaries.
The current demo focuses on application behaviour. Identity and network isolation are explicit
production gaps, not hidden assumptions.

