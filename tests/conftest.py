from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from procurepilot.api import create_app
from procurepilot.config import Settings


@pytest.fixture
def policy_directory() -> Path:
    return Path(__file__).parents[1] / "policies"


@pytest.fixture
def settings(tmp_path: Path, policy_directory: Path) -> Settings:
    return Settings(
        ai_provider="mock",
        database_path=tmp_path / "test.db",
        policy_directory=policy_directory,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def low_risk_payload() -> dict[str, object]:
    return {
        "requester": "Kadir Demir",
        "department": "Engineering",
        "vendor": "Contoso Tools GmbH",
        "amount_eur": 3_200,
        "description": "Developer tooling subscription for the engineering team.",
        "data_classification": "internal",
        "contains_personal_data": False,
        "single_source": False,
        "urgent": False,
    }


@pytest.fixture
def high_risk_payload() -> dict[str, object]:
    return {
        "requester": "Kadir Demir",
        "department": "Research & Development",
        "vendor": "Fabrikam Analytics Ltd",
        "amount_eur": 128_000,
        "description": "Quality inspection service processing images and employee identifiers.",
        "data_classification": "restricted",
        "contains_personal_data": True,
        "single_source": True,
        "urgent": True,
    }
