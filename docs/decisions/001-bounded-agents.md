# ADR-001: Bounded agents with deterministic orchestration

**Status:** Accepted  
**Date:** 2026-10-30

## Context

An unrestricted autonomous agent could retrieve policy, assess risk, approve a request and trigger an
external workflow. That design is difficult to evaluate and gives a probabilistic component authority
over a business control.

## Decision

ProcurePilot uses four bounded agents with explicit input and output contracts. The orchestration order
is deterministic. Approval thresholds, risk escalation and the human-review gate are implemented in
normal application code. The optional language model can only create the executive explanation.

## Consequences

- Approval behaviour is reproducible and covered by unit tests.
- Each agent can be observed, evaluated and replaced separately.
- A compromised prompt cannot directly approve a high-risk request.
- The approach is less flexible than a fully autonomous planner, by design.

