from pathlib import Path

import pytest

from procurepilot.models import (
    Assessment,
    AssessmentStatus,
    DataClassification,
    ProcurementRequest,
    Recommendation,
    ReviewDecision,
    RiskLevel,
)
from procurepilot.repository import AssessmentRepository


def pending_assessment() -> Assessment:
    return Assessment(
        request=ProcurementRequest(
            requester="Kadir Demir",
            department="Engineering",
            vendor="Contoso GmbH",
            amount_eur=30_000,
            description="Infrastructure monitoring subscription for production services.",
            data_classification=DataClassification.INTERNAL,
        ),
        status=AssessmentStatus.PENDING_REVIEW,
        risk_level=RiskLevel.MEDIUM,
        recommendation=Recommendation.REVIEW,
        approval_route=["line-manager", "procurement"],
        reasons=["Procurement review required."],
        executive_summary="Review is required.",
        policy_evidence=[],
        agent_trace=[],
        model_mode="deterministic-mock",
    )


def test_repository_review_roundtrip(tmp_path: Path) -> None:
    repository = AssessmentRepository(tmp_path / "repository.db")
    assessment = pending_assessment()
    repository.save(assessment)

    reviewed = repository.review(
        assessment.id,
        ReviewDecision(approved=True, reviewer="Jane Doe", note="Controls verified."),
    )

    assert reviewed is not None
    assert reviewed.status == AssessmentStatus.APPROVED
    assert reviewed.reviewed_at is not None
    assert repository.get(assessment.id) == reviewed


def test_repository_prevents_reviewing_final_assessment(tmp_path: Path) -> None:
    repository = AssessmentRepository(tmp_path / "repository.db")
    assessment = pending_assessment()
    assessment.status = AssessmentStatus.AUTO_APPROVED
    repository.save(assessment)

    with pytest.raises(ValueError, match="Only pending assessments"):
        repository.review(
            assessment.id,
            ReviewDecision(approved=True, reviewer="Jane Doe", note="Already final."),
        )
