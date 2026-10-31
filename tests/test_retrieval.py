from pathlib import Path

import pytest

from procurepilot.models import DataClassification, ProcurementRequest
from procurepilot.retrieval import PolicyRetriever


def test_retrieval_returns_ranked_policy_evidence(policy_directory: Path) -> None:
    retriever = PolicyRetriever(policy_directory)
    request = ProcurementRequest(
        requester="Kadir Demir",
        department="Research & Development",
        vendor="Fabrikam Analytics Ltd",
        amount_eur=80_000,
        description="AI cloud service processing confidential employee images.",
        data_classification=DataClassification.CONFIDENTIAL,
        contains_personal_data=True,
    )

    evidence = retriever.retrieve(request)

    assert len(evidence) == 4
    assert all(item.source == "procurement-policy.md" for item in evidence)
    assert any(item.section == "Data protection and security" for item in evidence)
    assert evidence[0].relevance >= evidence[-1].relevance


def test_retriever_rejects_empty_policy_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No policy sections"):
        PolicyRetriever(tmp_path)
