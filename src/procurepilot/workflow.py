from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import TypeVar

from opentelemetry import trace

from procurepilot.agents import NarrativeAgent, PolicyAgent, RiskAgent, RoutingAgent
from procurepilot.metrics import AGENT_DURATION, ASSESSMENTS
from procurepilot.models import AgentStep, Assessment, ProcurementRequest
from procurepilot.repository import AssessmentRepository

T = TypeVar("T")
tracer = trace.get_tracer(__name__)


class ProcurementWorkflow:
    """Deterministic orchestration around bounded, independently testable agents."""

    def __init__(
        self,
        policy_agent: PolicyAgent,
        risk_agent: RiskAgent,
        routing_agent: RoutingAgent,
        narrative_agent: NarrativeAgent,
        repository: AssessmentRepository,
    ) -> None:
        self._policy_agent = policy_agent
        self._risk_agent = risk_agent
        self._routing_agent = routing_agent
        self._narrative_agent = narrative_agent
        self._repository = repository

    @staticmethod
    async def _run_step(
        name: str,
        operation: Callable[[], Awaitable[T]],
    ) -> tuple[T, float]:
        started = perf_counter()
        with tracer.start_as_current_span(name):
            result = await operation()
        duration = perf_counter() - started
        AGENT_DURATION.labels(agent=name).observe(duration)
        return result, duration * 1_000

    async def assess(self, request: ProcurementRequest) -> Assessment:
        trace_steps: list[AgentStep] = []

        evidence, duration = await self._run_step(
            self._policy_agent.name, lambda: self._policy_agent.run(request)
        )
        trace_steps.append(
            AgentStep(
                agent=self._policy_agent.name,
                summary=f"Retrieved {len(evidence)} relevant policy sections.",
                duration_ms=duration,
            )
        )

        risk, duration = await self._run_step(
            self._risk_agent.name, lambda: self._risk_agent.run(request)
        )
        trace_steps.append(
            AgentStep(
                agent=self._risk_agent.name,
                summary=f"Classified the request as {risk.level.value} risk.",
                flags=risk.flags,
                duration_ms=duration,
            )
        )

        routing, duration = await self._run_step(
            self._routing_agent.name, lambda: self._routing_agent.run(request, risk)
        )
        trace_steps.append(
            AgentStep(
                agent=self._routing_agent.name,
                summary=f"Selected route: {', '.join(routing.approval_route)}.",
                flags=routing.flags,
                duration_ms=duration,
            )
        )

        narrative, duration = await self._run_step(
            self._narrative_agent.name,
            lambda: self._narrative_agent.run(request, risk, evidence),
        )
        trace_steps.append(
            AgentStep(
                agent=self._narrative_agent.name,
                summary="Generated a policy-grounded executive explanation.",
                duration_ms=duration,
            )
        )

        assessment = Assessment(
            request=request,
            status=routing.status,
            risk_level=risk.level,
            recommendation=routing.recommendation,
            approval_route=routing.approval_route,
            reasons=risk.reasons,
            executive_summary=narrative,
            policy_evidence=evidence,
            agent_trace=trace_steps,
            model_mode=self._narrative_agent.mode,
        )
        self._repository.save(assessment)
        ASSESSMENTS.labels(
            risk=assessment.risk_level.value,
            status=assessment.status.value,
            model_mode=assessment.model_mode,
        ).inc()
        return assessment
