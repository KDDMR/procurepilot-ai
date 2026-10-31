import pytest

from procurepilot.agents import RiskAgent, RoutingAgent
from procurepilot.models import (
    AssessmentStatus,
    DataClassification,
    ProcurementRequest,
    RiskLevel,
)


def request(**overrides: object) -> ProcurementRequest:
    values: dict[str, object] = {
        "requester": "Kadir Demir",
        "department": "Engineering",
        "vendor": "Contoso GmbH",
        "amount_eur": 1_000,
        "description": "Annual development tool subscription for the team.",
        "data_classification": DataClassification.INTERNAL,
    }
    values.update(overrides)
    return ProcurementRequest.model_validate(values)


@pytest.mark.parametrize(
    ("amount", "expected_risk", "expected_flag"),
    [
        (4_999, RiskLevel.LOW, None),
        (5_000, RiskLevel.MEDIUM, "manager_threshold"),
        (25_000, RiskLevel.MEDIUM, "procurement_threshold"),
        (100_000, RiskLevel.HIGH, "high_value"),
    ],
)
async def test_risk_thresholds(
    amount: float,
    expected_risk: RiskLevel,
    expected_flag: str | None,
) -> None:
    result = await RiskAgent().run(request(amount_eur=amount))

    assert result.level == expected_risk
    if expected_flag:
        assert expected_flag in result.flags
    else:
        assert result.flags == []


async def test_restricted_data_is_high_risk() -> None:
    result = await RiskAgent().run(request(data_classification=DataClassification.RESTRICTED))

    assert result.level == RiskLevel.HIGH
    assert "restricted_data" in result.flags


async def test_confidential_personal_data_requires_review() -> None:
    result = await RiskAgent().run(
        request(
            data_classification=DataClassification.CONFIDENTIAL,
            contains_personal_data=True,
        )
    )

    assert result.level == RiskLevel.MEDIUM
    assert "personal_confidential_data" in result.flags


async def test_single_source_and_urgency_do_not_bypass_controls() -> None:
    result = await RiskAgent().run(request(amount_eur=12_000, single_source=True, urgent=True))

    assert "single_source_exception" in result.flags
    assert "urgent_request" in result.flags


async def test_low_risk_request_is_auto_approved() -> None:
    procurement_request = request()
    risk = await RiskAgent().run(procurement_request)
    route = await RoutingAgent().run(procurement_request, risk)

    assert route.status == AssessmentStatus.AUTO_APPROVED
    assert route.approval_route == ["automated-policy-check"]


async def test_high_risk_route_is_deduplicated() -> None:
    procurement_request = request(
        amount_eur=150_000,
        single_source=True,
        data_classification=DataClassification.RESTRICTED,
    )
    risk = await RiskAgent().run(procurement_request)
    route = await RoutingAgent().run(procurement_request, risk)

    assert route.status == AssessmentStatus.PENDING_REVIEW
    assert route.approval_route == [
        "line-manager",
        "procurement",
        "executive-board",
        "security-and-data-protection",
    ]
