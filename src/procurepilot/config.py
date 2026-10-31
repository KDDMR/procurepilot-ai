from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ProcurePilot AI"
    environment: str = "development"
    log_level: str = "INFO"
    ai_provider: Literal["mock", "azure"] = "mock"

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = Field(default=None, repr=False)
    azure_openai_deployment: str = "gpt-4.1-mini"
    azure_openai_api_version: str = "2025-04-01-preview"

    database_path: Path = Path("procurepilot.db")
    policy_directory: Path = Path("policies")
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"

    @model_validator(mode="after")
    def validate_azure_configuration(self) -> "Settings":
        if self.ai_provider == "azure" and not (
            self.azure_openai_endpoint and self.azure_openai_api_key
        ):
            raise ValueError(
                "AI_PROVIDER=azure requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
