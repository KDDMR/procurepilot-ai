from dataclasses import dataclass

from procurepilot.llm import NarrativeProvider
from procurepilot.models import (
    AssessmentStatus,
    DataClassification,
    PolicyEvidence,
    ProcurementRequest,
    Recommendation,
    RiskLevel,
)
from procurepilot.retrieval import PolicyRetriever


@dataclass(frozen=True)
class RiskAssessment:
    level: RiskLevel
    reasons: list[str]
    flags: list[str]


@dataclass(frozen=True)
class RoutingDecision:
    status: AssessmentStatus
    recommendation: Recommendation
    approval_route: list[str]
    flags: list[str]


class PolicyAgent:
    name = "policy-agent"

    def __init__(self, retriever: PolicyRetriever) -> None:
        self._retriever = retriever

    async def run(self, request: ProcurementRequest) -> list[PolicyEvidence]:
        return self._retriever.retrieve(request)


class RiskAgent:
    name = "risk-agent"

    async def run(self, request: ProcurementRequest) -> RiskAssessment:
        reasons: list[str] = []
        flags: list[str] = []

        if request.amount_eur >= 100_000:
            flags.append("high_value")
            reasons.append("Requests of €100,000 or more require executive approval.")
        elif request.amount_eur >= 25_000:
            flags.append("procurement_threshold")
            reasons.append("Requests of €25,000 or more require Procurement review.")
        elif request.amount_eur >= 5_000:
            flags.append("manager_threshold")
            reasons.append("Requests of €5,000 or more require line-manager approval.")

        if request.data_classification == DataClassification.RESTRICTED:
            flags.append("restricted_data")
            reasons.append("Restricted data requires Security and Data Protection review.")
        elif (
            request.data_classification == DataClassification.CONFIDENTIAL
            and request.contains_personal_data
        ):
            flags.append("personal_confidential_data")
            reasons.append("Confidential personal data requires Data Protection review.")

        if request.single_source and request.amount_eur >= 10_000:
            flags.append("single_source_exception")
            reasons.append("A single-source purchase above €10,000 needs documented justification.")

        if request.urgent:
            flags.append("urgent_request")
            reasons.append("Urgency does not bypass the standard approval controls.")

        if "restricted_data" in flags or "high_value" in flags:
            level = RiskLevel.HIGH
        elif flags:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
            reasons.append("No elevated threshold or data-handling risk was detected.")

        return RiskAssessment(level=level, reasons=reasons, flags=flags)


class RoutingAgent:
    name = "routing-agent"

    async def run(
        self,
        request: ProcurementRequest,
        risk: RiskAssessment,
    ) -> RoutingDecision:
        route: list[str] = []

        if request.amount_eur >= 5_000:
            route.append("line-manager")
        if request.amount_eur >= 25_000 or "single_source_exception" in risk.flags:
            route.append("procurement")
        if request.amount_eur >= 100_000:
            route.append("executive-board")
        if any(flag in risk.flags for flag in ("restricted_data", "personal_confidential_data")):
            route.append("security-and-data-protection")

        if risk.level == RiskLevel.LOW:
            return RoutingDecision(
                status=AssessmentStatus.AUTO_APPROVED,
                recommendation=Recommendation.APPROVE,
                approval_route=["automated-policy-check"],
                flags=[],
            )

        return RoutingDecision(
            status=AssessmentStatus.PENDING_REVIEW,
            recommendation=Recommendation.REVIEW,
            approval_route=list(dict.fromkeys(route or ["procurement"])),
            flags=["human_approval_required"],
        )


class NarrativeAgent:
    name = "narrative-agent"

    def __init__(self, provider: NarrativeProvider) -> None:
        self._provider = provider

    @property
    def mode(self) -> str:
        return self._provider.mode

    async def run(
        self,
        request: ProcurementRequest,
        risk: RiskAssessment,
        evidence: list[PolicyEvidence],
    ) -> str:
        return await self._provider.summarise(request, risk.level, risk.reasons, evidence)
