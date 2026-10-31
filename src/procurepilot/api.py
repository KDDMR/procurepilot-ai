from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from procurepilot.agents import NarrativeAgent, PolicyAgent, RiskAgent, RoutingAgent
from procurepilot.config import Settings, get_settings
from procurepilot.llm import create_narrative_provider
from procurepilot.metrics import REVIEWS
from procurepilot.models import (
    Assessment,
    HealthResponse,
    ProcurementRequest,
    ReviewDecision,
)
from procurepilot.repository import AssessmentRepository
from procurepilot.retrieval import PolicyRetriever
from procurepilot.telemetry import configure_telemetry
from procurepilot.workflow import ProcurementWorkflow

STATIC_DIRECTORY = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_telemetry(runtime_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repository = AssessmentRepository(runtime_settings.database_path)
        retriever = PolicyRetriever(runtime_settings.policy_directory)
        narrative_provider = create_narrative_provider(runtime_settings)
        app.state.repository = repository
        app.state.workflow = ProcurementWorkflow(
            PolicyAgent(retriever),
            RiskAgent(),
            RoutingAgent(),
            NarrativeAgent(narrative_provider),
            repository,
        )
        yield

    app = FastAPI(
        title="ProcurePilot AI",
        version="0.1.0",
        description=(
            "Policy-aware agentic procurement automation with retrieval, explicit controls, "
            "human approval and an auditable execution trace."
        ),
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")

    @app.get("/", include_in_schema=False)
    async def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIRECTORY / "index.html")

    @app.get("/health", response_model=HealthResponse, tags=["Operations"])
    async def health() -> HealthResponse:
        return HealthResponse(status="healthy", ai_provider=runtime_settings.ai_provider)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post(
        "/api/v1/assessments",
        response_model=Assessment,
        status_code=status.HTTP_201_CREATED,
        tags=["Assessments"],
    )
    async def create_assessment(
        payload: ProcurementRequest,
        request: Request,
    ) -> Assessment:
        workflow: ProcurementWorkflow = request.app.state.workflow
        return await workflow.assess(payload)

    @app.get("/api/v1/assessments", response_model=list[Assessment], tags=["Assessments"])
    async def list_assessments(
        request: Request,
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[Assessment]:
        repository: AssessmentRepository = request.app.state.repository
        return repository.list(limit)

    @app.get(
        "/api/v1/assessments/{assessment_id}",
        response_model=Assessment,
        tags=["Assessments"],
    )
    async def get_assessment(assessment_id: UUID, request: Request) -> Assessment:
        repository: AssessmentRepository = request.app.state.repository
        assessment = repository.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return assessment

    @app.post(
        "/api/v1/assessments/{assessment_id}/decision",
        response_model=Assessment,
        tags=["Human review"],
    )
    async def review_assessment(
        assessment_id: UUID,
        decision: ReviewDecision,
        request: Request,
    ) -> Assessment:
        repository: AssessmentRepository = request.app.state.repository
        try:
            assessment = repository.review(assessment_id, decision)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        if assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not found")
        REVIEWS.labels(decision="approved" if decision.approved else "rejected").inc()
        return assessment

    if runtime_settings.otel_enabled:
        FastAPIInstrumentor.instrument_app(app)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("procurepilot.api:app", host="127.0.0.1", port=8000, reload=False)
