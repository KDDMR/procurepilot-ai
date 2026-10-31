# Five-minute interview demo

## 1. Frame the problem (30 seconds)

“ProcurePilot explores how agentic AI can automate a business process without handing an LLM control
over approvals. The use case is procurement request triage.”

## 2. Run a low-risk case (45 seconds)

Use the default €3,200 internal tooling request. Point out the automatic approval, retrieved policy
evidence and trace for all four agents.

## 3. Run an elevated-risk case (60 seconds)

Click **Load risky example**. The €128,000 request processes restricted data and uses a single source.
Show that the workflow selects Procurement, Executive Board and Security/Data Protection review.

## 4. Explain the design decision (60 seconds)

Open `docs/decisions/001-bounded-agents.md`. Explain that the LLM generates only the narrative;
thresholds and human-review gates remain deterministic and testable.

## 5. Show engineering quality (60 seconds)

Open the tests and GitHub Actions workflow. Mention API validation, CI, Docker, OpenTelemetry,
Prometheus and Bicep. Be explicit that Azure and Microsoft 365 are documented integration paths unless
you have deployed them yourself.

## 6. Discuss next steps (45 seconds)

Mention Entra ID/RBAC, governed policy ingestion, Azure AI Search, representative evaluation data and
Power Automate approval notifications.

